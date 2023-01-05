from starlette.applications import Starlette
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.staticfiles import StaticFiles
from endpoints import *
from link_endpoints import *
from templates import *
from websocket import *


routes = [
    WebSocketRoute('/database_ws', endpoint=database_ws),
    Route('/analytics', endpoint=analytics_endpoint, methods=['GET', 'POST']), Route('/', endpoint=main, methods=['GET']),
    Route('/location', endpoint=location, methods=['GET']), Route('/login', endpoint=login, methods=['GET', 'POST']),
    Route('/logout', endpoint=logout, methods=['GET']), Route('/confirm_email', endpoint=confirm_email, methods=['POST']),
    Route('/signup', endpoint=signup, methods=['GET']), Route('/set_cookie', endpoint=set_cookie, methods=['GET']),
    Route('/get_session', endpoint=get_session, methods=['GET']), Route('/register', endpoint=register, methods=['POST']),
    Route('/links', endpoint=links, methods=['GET']), Route('/delete', endpoint=delete, methods=['POST']),
    Route('/restore', endpoint=restore, methods=['POST']), Route('/update', endpoint=update, methods=['POST']),
    Route('/disable', endpoint=disable, methods=['POST']),
    Route('/sort', endpoint=sort, methods=['GET']), Route('/changevar', endpoint=change_var, methods=['POST']),
    Route('/addlink', endpoint=addlink, methods=['GET']), Route('/tutorial', endpoint=tutorial, methods=['POST']),
    Route('/tutorial_complete', endpoint=tutorial_complete, methods=['POST']),
    Route('/ads.txt', endpoint=ads, methods=['GET']), Route('/privacy', endpoint=privacy, methods=['GET']),
    Route('/unsubscribe', endpoint=unsubscribe, methods=['POST']), Route('/setoffset', endpoint=setoffset, methods=['POST']),
    Route('/add_number', endpoint=add_number, methods=['POST']), Route('/notes', endpoint=notes, methods=['GET', 'POST']),
    Route('/receive_vonage_message', endpoint=receive_vonage_message, methods=['GET', 'POST']),
    Route('/markdown_to_html', endpoint=markdown_to_html, methods=['POST']),
    Route('/reset', endpoint=reset_password, methods=['GET', 'POST']),
    Route('/reset-password', endpoint=send_reset_email, methods=['POST', 'GET']),
    Route('/tutorial_changed', endpoint=tutorial_changed, methods=['GET']),
    Route('/open_early', endpoint=open_early, methods=['POST']), Route('/robots.txt', endpoint=robots, methods=['GET']),
    Route('/send_message', endpoint=send_message, methods=['POST']), Route('/favicon.ico', endpoint=favicon, methods=['GET']),
    Route('/add_accounts', endpoint=add_accounts, methods=['POST']),
    Route('/invalidate-token', endpoint=invalidate_token, methods=['POST']),
    Route('/images/loading2.gif', endpoint=loading, methods=['GET']),
    Route('/validatetoken', endpoint=validatetoken, methods=['POST']),
    Route('/verify_session', endpoint=verify_session, methods=['GET']),
    Route('/get_open_early', endpoint=get_open_early, methods=['GET']),
    Route('/link', endpoint=link, methods=['GET']),
    Route('/database', endpoint=database, methods=['GET']),
    Route('/pricing', endpoint=pricing, methods=['GET']),
    Route('/updatetimezone', endpoint=update_timezone, methods=['POST']),
    Route('/daylightsavings', endpoint=daylight_savings, methods=['POST']),
    Route('/share-link', endpoint=share_link, methods=['POST']),
    Route('/accept-link', endpoint=accept_link, methods=['POST']),
    Route('/disable-all', endpoint=disable_all, methods=['POST']),
    Route('/org_disabled', endpoint=org_disabled, methods=['GET']),
    Mount('/static', StaticFiles(directory='static'), name='globals.js'),
    Mount('/static', StaticFiles(directory='static'), name='redirect.js'),
    Mount('/static', StaticFiles(directory='static'), name='.DS_Store'),
    Mount('/static', StaticFiles(directory='static'), name='notes.js'),
    Mount('/static', StaticFiles(directory='static'), name='links.js'),
    Mount('/static', StaticFiles(directory='static'), name='login.css'),
    Mount('/static', StaticFiles(directory='static'), name='website.css'),
    Mount('/static', StaticFiles(directory='static'), name='link.css'),
    Mount('/static', StaticFiles(directory='static'), name='pricing.css'),
    Mount('/static', StaticFiles(directory='static'), name='links.css'),
    Mount('/static', StaticFiles(directory='static'), name='premium.css'),
    Mount('/static', StaticFiles(directory='static'), name='premium.js'),
    Mount('/static', StaticFiles(directory='static'), name='forgot-password.css'),
    Mount('/static', StaticFiles(directory='static'), name='new_links.css'),
    Mount('/static', StaticFiles(directory='static'), name='manifest.json'),
    Mount('/static', StaticFiles(directory='static'), name='serviceworker.js'),
    Mount('/static', StaticFiles(directory='static'), name='privacy.css'),
    Mount('/static', StaticFiles(directory='static'), name='globals.css'),
    Mount('/static', StaticFiles(directory='static'), name='aa4e.css'),
    Mount('/static/images', StaticFiles(directory='static'), name='check-square.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='arrow-down.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='list.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='paper-plane-2.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='from.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='arrows-down.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='linkjoin-homepage.png'),
    Mount('/static/images', StaticFiles(directory='static'), name='whiteboard.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='github.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='calendar_guy.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='website.png'),
    Mount('/static/images', StaticFiles(directory='static'), name='angle-down.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='links_loader.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='lock.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='pen.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='link.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='arrow-right.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='envelope.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='time.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='right-angle.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='404.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='plus-mobile.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='meeting.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='plus.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='why_linkjoin.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='text.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='curve.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='paper-plane.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='linkjoin-links-page.png'),
    Mount('/static/images', StaticFiles(directory='static'), name='link_footer.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='logo-text.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='trash.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='links_page.png'),
    Mount('/static/images', StaticFiles(directory='static'), name='check-box.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='mobile-phone.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='phone.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='logo-rounded.png'),
    Mount('/static/images', StaticFiles(directory='static'), name='discord.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='arrow-left.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='ellipsis.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='logo.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='mouse-pointer.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='heart.svg'),
    Mount('/static/images', StaticFiles(directory='static'), name='loading2.gif'),
    Mount('/static/images', StaticFiles(directory='static'), name='undo.svg')
]




app = Starlette(routes=routes, debug=False, exception_handlers={404: not_found}, on_startup=[lambda: print('Started app.')])
