"""MCP server, so AI assistants like Claude can look up college sports with ncaapyscraper.
Runs on the user's machine over stdio, start it with ncaapyscraper-mcp."""

import functools

try:
    from mcp.server import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:
    raise ImportError('The MCP server needs the mcp package, pip install "ncaapyscraper[mcp]"') from None

from ncaapyscraper import api
from ncaapyscraper.constants import NCAA_SPORTS


server = MCPServer(
    'ncaapyscraper',
    instructions=(
        "College sports data. Rosters, coaches and schedules come from each school's own athletics site, "
        'find the school key with list_schools first. Scores, box scores, rankings, standings and stat leaders '
        f'come from ncaa.com, its sports are {", ".join(NCAA_SPORTS)}. Divisions are d1, d2, d3, fbs or fcs.'
    ),
    log_level='WARNING',
)


def tool(function):
    "Registers a tool. Errors we expect (unknown sport, a page down) go back to the model as text, not a crash"
    @functools.wraps(function)
    async def wrapper(*args, **kwargs):
        try:
            return await function(*args, **kwargs)
        except (ValueError, ConnectionError) as error:
            raise ToolError(str(error)) from error

    return server.tool()(wrapper)


@tool
async def list_schools(search: str | None = None, conference: str | None = None, division: str | None = None) -> list[dict]:
    "Supported schools and their key. search matches the name or key, conference like sec or big10, division 1, 2, 3, fbs or fcs"
    schools = api.list_schools(conference, division)
    if search:
        schools = [school for school in schools if search.lower() in f"{school['key']} {school['name']}".lower()]

    return schools


@tool
async def get_roster(school: str, sport: str | None = None) -> list[dict]:
    "Athletes on a school's teams. school is a key from list_schools or the athletics site, sport like football or mens-basketball"
    return await api.fetch_roster(school, sport, bios=False)


@tool
async def get_coaches(school: str, sport: str | None = None) -> list[dict]:
    "Coaches and support staff of a school's teams"
    return await api.fetch_coaches(school, sport, bios=False)


@tool
async def get_schedule(school: str, sport: str | None = None) -> list[dict]:
    "A school's games this season with results, score is always the school's score first"
    return await api.fetch_schedule(school, sport)


@tool
async def get_scoreboard(sport: str, date: str | None = None, division: str | None = None, week: int | None = None) -> list[dict]:
    "Every game on a date (YYYY-MM-DD, default today). Football goes by week instead, default the current week"
    return await api.fetch_scoreboard(sport, date, division, week)


@tool
async def get_boxscore(game_id: str, sport: str | None = None) -> list[dict]:
    "Player stats for one game, game_id comes from get_scoreboard"
    return await api.fetch_boxscore(game_id, sport)


@tool
async def get_rankings(sport: str, division: str | None = None, poll: str | None = None) -> list[dict]:
    "Polls like the AP Top 25. poll is the end of the ncaa.com rankings url (associated-press), default is the main poll"
    return await api.fetch_rankings(sport, division, poll)


@tool
async def get_standings(sport: str, division: str | None = None) -> list[dict]:
    "Conference standings, conference and overall records for every team"
    return await api.fetch_standings(sport, division)


@tool
async def list_stats(sport: str, division: str | None = None) -> list[dict]:
    "Stats ncaa.com ranks national leaders for, use a name from here with get_stat_leaders"
    return await api.fetch_stat_list(sport, division)


@tool
async def get_stat_leaders(sport: str, stat: str, division: str | None = None, team: bool = False) -> list[dict]:
    "National leaders for one stat, e.g. Rushing Yards. team=True for team stats like Scoring Offense"
    return await api.fetch_stats(sport, stat, division, team)


def main():
    server.run()


if __name__ == '__main__':
    main()
