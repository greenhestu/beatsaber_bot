'''Slash commands with button-based sub-actions. Requires discord.py >= 2.0.

/info [player]      ScoreSaber profile embed
                    buttons: History / Graph / Farm picks
/recommend [map] [count]
                    map given  -> similar maps (ScoreSaber or BeatLeader,
                                  auto-detected from the link/id)
                    map empty  -> similar higher-pp users + farm picks
                                  for your registered account
                    buttons: Playlist (.bplist) / More

Registered from discord_bot.py via setup(bot).
'''
import asyncio, os, re
import discord
import requests
from discord import app_commands
from bot_command_set import did_sc, DrawingGraph
from bot_command_set import path as PP_PATH, ENCODING, ERRORS

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
RECOMMEND_DIR = os.path.join(DIR_PATH, 'recommend')
SS_API = 'https://scoresaber.com/api/player/'
MAX_COUNT = 15  # discord 2000자 제한

# ---------------------------------------------------------------- helpers
def resolve_sc_id(interaction, player):
    '''player 인자(주소/id) 또는 호출자의 등록 계정에서 스코어세이버 id를 얻는다'''
    if player:
        m = re.findall(r'\d{10,}', player)
        return m[0] if m else None
    return did_sc.get(str(interaction.user.id))

def fetch_profile(sc_id):
    try:
        r = requests.get(SS_API + str(sc_id) + '/full', timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

def profile_embed(d):
    stats = d.get('scoreStats') or {}
    desc = (f"Global Rank: #{d['rank']}\n"
            f"{d['country']} Rank: #{d['countryRank']}\n"
            f"PP: {d['pp']:.2f}pp\n"
            f"Avg Ranked Acc: {stats.get('averageRankedAccuracy', 0):.2f}%\n"
            f"Total Play Count: {stats.get('totalPlayCount', '?')}")
    e = discord.Embed(title=f"{d['name']}'s profile",
                      url=f"https://scoresaber.com/u/{d['id']}",
                      description=desc, color=0x00ff56)
    if d.get('profilePicture'):
        e.set_thumbnail(url=d['profilePicture'])
    return e

def read_history(sc_id, n=20):
    '''일일 기록 파일(data/PP_text/<id>.txt)의 최근 n줄'''
    try:
        with open(PP_PATH + str(sc_id) + '.txt', 'r',
                  encoding=ENCODING, errors=ERRORS) as f:
            lines = [l for l in f.readlines() if l.strip() and l != 'nextmonth\n']
    except (FileNotFoundError, OSError):
        return None
    return lines[-n:] if lines else None

def draw_history_graph(sc_id, n=40):
    lines = read_history(sc_id, n)
    if not lines or len(lines) < 2:
        return False
    name = lines[-1].split(':')[-1].strip()
    historylist = [l.split(',')[0:2] for l in lines]
    historylist.reverse()
    DrawingGraph(name, historylist)  # graph.png 저장
    return True

async def run_similar(tool, target, num, playlist_path=None):
    '''recommend/<tool>/similar.py 실행 (로컬 DB만 읽음, API 호출 없음)'''
    script = os.path.join(RECOMMEND_DIR, tool, 'similar.py')
    cmd = ['python3', script, str(target), str(num)]
    if playlist_path is not None:
        cmd.append('--playlist=' + playlist_path)
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    out, _ = await proc.communicate()
    return out.decode('utf-8', 'ignore').strip()

def clip(text, limit=1900):
    return text if len(text) <= limit else text[:limit] + '\n...(truncated)'

def parse_map_arg(map_arg):
    '''리더보드 주소/id에서 (tool, target) 판별. 숫자만이면 ScoreSaber.'''
    m = re.search(r'global/([0-9a-fx]+)', map_arg)
    if m:
        return 'bl_maps', m.group(1)
    token = map_arg.rstrip('/').split('/')[-1]
    if token.isdecimal() and 'beatleader' not in map_arg:
        nums = re.findall(r'\d+', map_arg)
        return 'ss_maps', nums[-1]  # map/<id>/difficulty/<lb_id> 형태 대응
    return 'bl_maps', token

# ---------------------------------------------------------------- views
class InfoView(discord.ui.View):
    '''프로필 embed 아래 세부 기능 버튼'''
    def __init__(self, sc_id):
        super().__init__(timeout=600)
        self.sc_id = sc_id

    @discord.ui.button(label='History', emoji='📜', style=discord.ButtonStyle.primary)
    async def history_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        lines = read_history(self.sc_id)
        if not lines:
            await interaction.response.send_message(
                'No recorded history for this player. Add them with `!추가` first.',
                ephemeral=True)
            return
        await interaction.response.send_message(
            '```' + clip(''.join(lines)) + '```', ephemeral=True)

    @discord.ui.button(label='Graph', emoji='📈', style=discord.ButtonStyle.primary)
    async def graph_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True)
        ok = await asyncio.get_event_loop().run_in_executor(
            None, draw_history_graph, self.sc_id)
        if not ok:
            await interaction.followup.send(
                'Not enough recorded history to draw a graph.')
            return
        await interaction.followup.send(
            file=discord.File(os.path.join(os.getcwd(), 'graph.png')))

    @discord.ui.button(label='Farm picks', emoji='🌾', style=discord.ButtonStyle.success)
    async def farm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True)
        answer = await run_similar('ss_users', self.sc_id, 8)
        if not answer:
            await interaction.followup.send('Recommendation data is not ready.')
            return
        await interaction.followup.send(
            '```' + clip(answer) + '```',
            view=RecommendView('ss_users', self.sc_id, 8))


class RecommendView(discord.ui.View):
    '''추천 결과 아래 세부 기능 버튼'''
    def __init__(self, tool, target, count):
        super().__init__(timeout=600)
        self.tool = tool
        self.target = target
        self.count = count

    @discord.ui.button(label='Playlist', emoji='📥', style=discord.ButtonStyle.success)
    async def playlist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True)
        pl_path = os.path.join(RECOMMEND_DIR, f'pl_{self.tool}_{self.target}.bplist')
        await run_similar(self.tool, self.target, self.count, pl_path)
        if not os.path.exists(pl_path):
            await interaction.followup.send('Could not build a playlist for this result.')
            return
        await interaction.followup.send(
            file=discord.File(pl_path, filename=f'similar_{self.target}.bplist'))
        os.remove(pl_path)

    @discord.ui.button(label='More', emoji='➕', style=discord.ButtonStyle.secondary)
    async def more_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.count >= MAX_COUNT:
            await interaction.response.send_message(
                f'Already showing the maximum of {MAX_COUNT} results.', ephemeral=True)
            return
        self.count = min(self.count + 7, MAX_COUNT)
        answer = await run_similar(self.tool, self.target, self.count)
        await interaction.response.edit_message(
            content='```' + clip(answer) + '```', view=self)


# ---------------------------------------------------------------- commands
def setup(bot):
    @bot.tree.command(name='info', description='Look up a ScoreSaber profile')
    @app_commands.describe(
        player='ScoreSaber profile URL or id (empty = your registered account)')
    async def info(interaction: discord.Interaction, player: str = None):
        sc_id = resolve_sc_id(interaction, player)
        if sc_id is None:
            await interaction.response.send_message(
                'No account found. Register with `!등록 <ScoreSaber URL>` '
                'or pass a profile URL/id.', ephemeral=True)
            return
        await interaction.response.defer(thinking=True)
        profile = await asyncio.get_event_loop().run_in_executor(
            None, fetch_profile, sc_id)
        if profile is None:
            await interaction.followup.send(
                'Could not reach ScoreSaber. Check the id or try again later.')
            return
        await interaction.followup.send(
            embed=profile_embed(profile), view=InfoView(sc_id))

    @bot.tree.command(name='recommend',
                      description='Recommend ranked maps (or similar players to learn from)')
    @app_commands.describe(
        map='Leaderboard URL or id, ScoreSaber/BeatLeader (empty = personal picks '
            'based on your registered account)',
        count='Number of results, max 15 (default 8)')
    async def recommend(interaction: discord.Interaction,
                        map: str = None, count: int = 8):
        count = max(1, min(count, MAX_COUNT))
        if map is None:
            sc_id = did_sc.get(str(interaction.user.id))
            if sc_id is None:
                await interaction.response.send_message(
                    'Register with `!등록 <ScoreSaber URL>` first, '
                    'or pass a leaderboard link.', ephemeral=True)
                return
            tool, target = 'ss_users', sc_id
        else:
            tool, target = parse_map_arg(map)
        await interaction.response.defer(thinking=True)
        answer = await run_similar(tool, target, count)
        if not answer:
            await interaction.followup.send(
                'Recommendation data is not ready. Ask the admin to run the '
                'fetch scripts in recommend/.')
            return
        await interaction.followup.send(
            '```' + clip(answer) + '```', view=RecommendView(tool, target, count))
