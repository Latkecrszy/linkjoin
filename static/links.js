let global_username, global_sort, tutorial_complete, global_links
let tutorial_active = false;
let created = false;
let connected = true;
const notesInfo = {}

window.addEventListener('offline', () => {connected = false; console.log('disconnected')})
window.addEventListener('online', async () => {console.log('reconnected'); location.reload()})

document.addEventListener('click', (e) => {
    if (!e.target.parentElement.classList.contains('demo')) {
        document.getElementById('tutorial-menu').style.display = 'none'
    }
    else if (!e.target.classList.contains('menu_buttons')) {
        closeTutorial()
    }
    if ((e.target.id !== 'open-tutorial' && !document.getElementById('tutorial').contains(e.target)
        && e.target.id !== 'tutorial') || (e.target.parentElement.classList.value === 'menu tutorial'
        || e.target.parentElement.parentElement.classList.value === 'menu tutorial') && e.target.innerText !== 'Copy link'){
        closeTutorial()
    }
})


function createElement(tag, classList=[], id='', text='', other={}) {
    const el = document.createElement(tag)
    classList.forEach((i) => el.classList.add(i))
    el.innerText = text
    if (id !== '') {
        el.id = id
    }

    for (const [key, value={}] of Object.entries(other)) {
        if (key === 'events') {
            for (const [name, event] of Object.entries(value)) {
                el[name] = event
            }
        } else if (key === 'style') {
            for (const [name, style] of Object.entries(value)) {
                el.style[name] = style
            }
        } else if (key === 'attrs') {
            for (const [name, attr] of Object.entries(value)) {
                el.setAttribute(name, attr)
            }
        }
    }

    return el
}

function openMenu(el) {
    el.children[el.children.length-1].style.display = 'flex';
}

function blur(show) {
    document.getElementById("blur").style.opacity = show ? "0.4" : "0"
    document.getElementById("blur").style.zIndex = show ? "3" : "-3"
}

function getOffset(el) {
    const rect = el.getBoundingClientRect();
    return {
        left: rect.left + window.scrollX,
        top: rect.top + window.scrollY
    }
}

async function db(username, id) {
    const deleted = id === 'deleted-links-body' ? 'true' : 'false'
    let results = connected ? await fetch('/db', {headers: {email: username, deleted: deleted}}).then(response => response.json()) : global_links || []
    if (results['error'] === 'Forbidden') {return location.reload()}
    return results
}

async function popUp(popup) {
    if (confirmed === 'false') {
        if (popup === 'popup') {
            return await sendNotif(`Before you make your first link, please check your inbox for ${global_username} to confirm your email address.`, '#ba1a1a')
        }
        return await sendNotif(`Check your inbox for ${global_username} to confirm your email address.`, '#ba1a1a')
    }
    hide('popup')
    document.getElementById(popup).style.display = "flex"
    const submit = document.getElementById("submit")
    blur(true)
    submit.innerHTML = `Create <img src="/static/images/right-angle.svg" alt="right arrow">`
    submit.setAttribute('onClick', "registerLink('register')")
    document.getElementById("name").value = null
    document.getElementById("link").value = null
    document.getElementById("hour").placeholder = 1
    document.getElementById("hour").value = null
    document.getElementById("minute").placeholder = '00'
    document.getElementById("minute").value = null
    document.getElementById("password").value = null
    document.getElementById("title").innerText = "Schedule a new meeting"
    document.getElementById('week').selected = "selected"
    for (let child of document.getElementById("days").children) {
        if (child.value !== ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][date.getDay()]) {
            child.classList.remove("selected")
        }
    }
    document.getElementById("0").selected = "selected"
}

function hide(popup, showBlur=false) {
    document.getElementById(popup).style.display = "none"
    blur(showBlur)
}

function edit(link) {
    const element = document.getElementById("popup")
    element.style.display = "flex"
    blur(true)
    if (link === 'tutorial') {
        document.getElementById("title").innerText = "Edit your meeting";
        document.getElementById("submit").innerHTML = `Update <img src="/static/images/right-angle.svg" alt="right arrow">`
        document.getElementById("name").value = 'Tutorial Link'
        document.getElementById("link").value = 'https://linkjoin.xyz';
        document.getElementById("pm").selected = "selected";
        document.getElementById("hour").placeholder = 12;
        document.getElementById("minute").placeholder = "00";
        ['Mon', 'Tue'].forEach(day => document.getElementById(day).classList.add("selected"))
        return document.getElementById("submit").setAttribute('onClick', "registerLink('tutorial')")
    }
    document.getElementById("name").value = link["name"]
    document.getElementById("link").value = link["link"]
    document.getElementById("text_select").value = link["text"].toString()
    document.getElementById("starts_select").value = (parseInt(link["starts"])%5).toString()
    if ("password" in link) {document.getElementById("password").value = link["password"]}
    else {document.getElementById("password").value = null}
    if (parseInt(link['time'].split(":")[0]) === 12) {
        document.getElementById("pm").selected = "selected"
        document.getElementById("hour").placeholder = 12
    }
    else if (parseInt(link['time'].split(":")[0]) === 24) {document.getElementById("hour").value = 12}
    else if (parseInt(link['time'].split(":")[0]) > 12) {
        document.getElementById("hour").value = parseInt(link['time'].split(":")[0])-12
        document.getElementById("pm").selected = "selected"
    }
    else {document.getElementById("hour").value = parseInt(link['time'].split(":")[0])}
    document.getElementById("minute").value = link['time'].split(":")[1]
    document.getElementById("submit").innerHTML = `Update <img src="/static/images/right-angle.svg" alt="right arrow">`
    document.getElementById("submit").setAttribute('onClick', `registerLink(${link['id']})`)
    document.getElementById("title").innerText = "Edit your meeting";
    ["Sun", "Mon","Tue", "Wed", "Thu", "Fri", "Sat"].forEach(i => document.getElementById(i).classList.remove("selected"))
    link['days'].forEach(day => {if (document.getElementById(day)) {document.getElementById(day).classList.add("selected")}})
    document.getElementById(link['repeat']).selected = "selected"
    window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
    link['starts'] ? document.getElementById((link['starts']/link['days'].length).toString()).selected = "selected" : null
}

async function delete_(link) {
    window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
    document.getElementById("popup_delete").style.display = "flex"
    if (link === 'tutorial') {
        document.getElementById("popup_delete").children[0].innerHTML = 'Are you sure you want to delete <b>Tutorial</b>?'
        return document.getElementById("delete_button").addEventListener('click', () => {location.reload()})
    }
    document.getElementById("popup_delete").children[0].innerHTML = 'Are you sure you want to delete <b>'+link['name']+'</b>?'
    document.getElementById("delete_button").addEventListener('click', async () => {
        hide('popup_delete')
        await fetch('/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: link['id'], email: link['username']})
        })
        if ((await db(global_username)).length === 0) {return location.reload()}
        await refresh()
        await load_links(link['username'], global_sort)
    })
    blur(true)
}

function share(link) {
    document.getElementById("popup_share").style.zIndex = "11"
    document.getElementById("popup_share").style.display = {"none": "flex", "flex": "none"}[document.getElementById("popup_share").style.display]
    document.getElementById("share_link").value = link === 'tutorial' ? 'https://linkjoin.xyz/addlink?id=tutorial' : link['share']
    blur(true)
    window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
}

async function disable(link, username) {
    await fetch('/disable', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: link['username'], id: link['id']})
    })
    await refresh()
    await load_links(username, global_sort)
}

function copyPassword(id, password) {
    navigator.clipboard.writeText(password).then(async () => {
        document.getElementById(id).innerText = "Copied!"
        await sleep(2000)
        document.getElementById(id).innerText = "Password"
    })
}

function copyLink(link, id) {
    if (link === 'tutorial') {
        return navigator.clipboard.writeText('https://linkjoin.xyz')
    }
    navigator.clipboard.writeText(link).then(async () => {
        document.getElementById(id).innerText = "Copied!"
        await sleep(2000)
        document.getElementById(id).innerText = "Copy link"
    })
}

function permDelete(link) {
    hide('deleted-links', true)
    window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
    document.getElementById("popup_delete").style.display = "flex"
    document.getElementById("popup_delete").children[0].innerHTML = 'Are you sure you want to permanently delete <b>'+link['name']+'</b>? This action cannot be undone.'
    document.getElementById("delete_button").addEventListener('click', async () => {
        hide('popup_delete')
        await fetch('/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: link['id'], email: link['username'], permanent: 'true'})
        })
        location.reload()
    })
}

async function restore(id, email) {
    await fetch('/restore', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: id, email: email})
    })
    location.reload()
}

async function load_links(username, sort, id="insert") {
    const cookieSessionId = document.cookie.match('(^|;)\\s*session_id\\s*=\\s*([^;]+)')?.pop() || ''
    const sessionIds = await fetch('/get_session', {headers: {'email': username, 'token': token}}).then(id => id.json())
    if (sessionIds === null || !sessionIds.includes(cookieSessionId)) {location.replace('/login?error=not_logged_in')}
    global_username = username
    global_sort = sort
    try {
        document.getElementById(id).style.display = 'flex'
    }
    catch {
        while (!connected) {
            await sleep(5000)
        }
        location.reload()
    }
    if (id === 'deleted-links') {id = 'deleted-links-body'}
    const insert = document.getElementById(id)
    for (let i=0; i<3; i++) {insert.innerHTML += '<div class="placeholder"></div>'}
    const links = await db(username, id)
    global_links = links
    if (id !== 'insert') {
        blur(true)
    }
    if (links.toString() === '' && id === 'insert') {
        await refresh(id)
        document.getElementById("header_links").style.margin = "0 0 0 0"
        document.getElementById("disappear").classList.remove("gone")
    }
    else if (links.toString() === '' && id !== 'insert') {
        insert.classList.add('empty')
        return insert.innerHTML = `<h2>After you delete a link, it will show up here.</h2>
                            <img src="/static/images/trash.svg" alt="trash can">
                            `
    }
    else {
        let final = []
        if (sort === "day") {
            const link_list = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": [], "Sat": [], "Sun": []}
            for (const link_info of links) {link_list[link_info['days'][0]].push(link_info)}
            for (const day in link_list) {for (let key of link_list[day]) {final.push(key)}}
        }
        else if (sort === "time") {
            const times = []
            let added_time = 0.0000001
            const add = {"Sun": 0.001, "Mon": 0.002, "Tue": 0.003, "Wed": 0.004, "Thu": 0.005, "Fri": 0.006, "Sat": 0.007}
            const time_links_list = {}
            for (const link_info of links) {
                times.push(parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`)+add[link_info['days'][0]]+added_time)
                time_links_list[parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`)+add[link_info['days'][0]]+added_time] = link_info
                added_time += 0.0000001
            }
            for (const link_time of times.sort((a, b) => a - b)) {final.push(time_links_list[link_time])}
            const link_list = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": [], "Sat": [], "Sun": []}
            for (const link_info of final) {link_list[link_info['days'][0]].push(link_info)}
        }
        else if (sort === "datetime") {
            let added_time = 0.0000001
            const link_dict = {"Mon": {}, "Tue": {}, "Wed": {}, "Thu": {}, "Fri": {}, "Sat": [], "Sun": {}, "dates": {}}
            const other_link_list = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": [], "Sat": [], "Sun": [], "dates": []}
            for (const link_info of links) {
                link_dict[link_info['days'][0]][parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`)+added_time] = link_info
                other_link_list[link_info['days'][0]].push(parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`)+added_time)
                added_time += 0.0000001
            }
            for (const day_name in other_link_list) {
                other_link_list[day_name] = other_link_list[day_name].sort((a, b) => a - b)
            }
            for (const day_name in other_link_list) {
                for (let time_info of other_link_list[day_name]) {final.push(link_dict[day_name][time_info])}
            }
        }
        else {final = links}
        let iterator = 0;
        const checked = []
        await refresh(id)
        for (const link of final) {
            let hour = link["time"].split(":")[0]
            let meridian = "am"
            if (parseInt(hour) === 12) {meridian = "pm"}
            else if (parseInt(hour) === 24) {hour = 12}
            else if (parseInt(hour) > 12) {hour = parseInt(hour) - 12; meridian = "pm"}
            const time = `${hour}:${link["time"].split(":")[1]} ${meridian}`
            let link_event;

            link_event = createElement('div', ['link'])
            if (link['active'] === 'false') {
                link_event.classList.add('link-disabled')
            }
            link_event.appendChild(createElement('p', ['time'], '', time))
            const joinMeeting = createElement('div', ['join-meeting'], '', '',
                {'events': {'onclick': () => {window.open(link['link'])}}})
            joinMeeting.appendChild(createElement('p', ['name'], '', link['name']))
            joinMeeting.appendChild(createElement('p', ['description'], '', 'Click to join the meeting now'))
            link_event.appendChild(joinMeeting)
            link_event.appendChild(createElement('p', ['days'], '', link['days'].join(", ")))
            if (id === "insert") {
                link_event.appendChild(createElement('input', ['switch-checkbox'], `switch${iterator}`,
                    '', {'attrs': {'type': 'checkbox'}}))
                link_event.appendChild(createElement('label', ['switch'], '', '',
                    {'attrs': {'for': `switch${iterator}`}, 'events': {'onclick': () => {disable(link, username)}}}))
            }
            link_event.appendChild(createElement('img', ['dot-menu'], '', '',
                {'attrs': {'src': 'static/images/ellipsis.svg', 'alt': '3 dots'}, 'events': {'onclick': () => {openMenu(link_event)}}}))
            link_event.appendChild(createElement('img', ['link-expand'], '', '',
                {'events': {'onclick': () => link_event.classList.toggle('expanded')},
                    'attrs': {'src': 'static/images/angle-down.svg', 'alt': 'down arrow'}}))
            const menu = createElement('div', ['menu'])
            let buttons;
            if (id === "insert") {
                buttons = {'Edit': () => edit(link), 'Delete': () => delete_(link), 'Share': () => share(link),
            'Notes': () => createNote(link['name'], link['id']), 'Copy link': () => copyLink(link['link'], link['id']),
            'Password': () => copyPassword(link['id'], link['password'])}
            } else {
                buttons = {'Restore': () => restore(link['id'], link['username']), 'Delete': () => permDelete(link),
                    'Notes': () => createNote(link['name'], link['id']), 'Copy link': () => copyLink(link['name'], link['id']),
                    'Password': () => copyPassword(link['id'], link['password'])}
            }
            for (const [key, value] of Object.entries(buttons)) {
                if (key === 'Password' && link['password'] === undefined && id === 'insert') {continue}
                else if (key === 'Password' && link['password'] === undefined) {menu.style.height = '145px'; continue}
                else if (key === 'Password' && id === "insert") {menu.style.height = '230px'}
                menu.appendChild(createElement('div', [], '', key, {'events': {'onclick': value}}))
                key !== (link['password'] !== undefined ? 'Password' : 'Copy link') ? menu.appendChild(createElement('hr', ['menu_line'])) : null
            }
            link_event.appendChild(menu)
            checked.push(link['active'] === 'true')
            insert.appendChild(link_event)
            iterator += 1
        }
        if (id === 'insert') {
            document.addEventListener('click', e => {
                Array.from(document.getElementsByClassName('menu')).forEach(i => {
                    if (!['Copied!', 'Password', 'Copy link'].includes(e.target.innerText) && !e.target.classList.contains('dot-menu')
                        && !i.classList.contains('tutorial')) {
                        i.style.display = 'none'
                    }
                })
            })
        }

        try {
            checked.forEach((Checked, index) => {if (Checked) {document.getElementById('switch'+index).checked = 'checked'}})
        }
        catch {}
    }
    const clickToCopy = document.getElementById("click_to_copy")
    clickToCopy.addEventListener('click', async () => {
        navigator.clipboard.writeText(document.getElementById("share_link").value).then(async () => {
            clickToCopy.innerText = "Copied!"
            await sleep(2000)
            clickToCopy.innerText = "Click to Copy"
        })
    })
    let tutorial_completed = await fetch('/tutorial_complete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({'email': username})})
    tutorial_completed = await tutorial_completed.json()
    if (tutorial_completed['tutorial'] !== "done") {await popupWarn(tutorial_completed['tutorial'])}
    await check_day(username)
    await checkTutorial()
    clearInterval(open)
    if (error === 'link_not_found') {
        history.pushState('data', 'LinkJoin', '/links')
        await sendNotif('The link you are trying to add could not be found. Please contact the owner of this link for more information.', '#ba1a1a')
    }
    start(username, links, sort)
    if (document.getElementsByClassName('highlight').length > 0) {
        document.getElementsByClassName('highlight')[0].scrollIntoView(true)
        await sleep(3000)
        document.getElementsByClassName('highlight')[0].style.background = 'none'
    }

}

async function check_day(username) {
    let date = new Date()
    const links = await db(username)
    let day = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[date.getDay()]
    let children = document.getElementById("days").children
    if (links.length <= 3) {
        for (let child of children) {
            if (child.value === day) {child.classList.add("selected")}
        }
    }
}

async function sort() {
    location.replace("/sort?sort="+document.getElementsByClassName("sort")[0].value.toString())
}


async function registerLink(parameter) {
    disableButton(document.getElementById('submit'))
    if (created) {return}
    if (parameter === 'tutorial') {location.reload()}
    created = true
    let hour = parseInt(document.getElementById("hour").value || document.getElementById("hour").placeholder)
    let minute = parseInt(document.getElementById("minute").value || document.getElementById("minute").placeholder)
    if (minute.toString().length === 1) {minute = '0' + minute}
    if (document.getElementById("am").value === "pm") {if (hour !== 12) {hour += 12}}
    else {if (hour === 12) {hour += 12}}
    let days = []
    for (let child of document.getElementById("days").children) {
        if (child.classList.contains("selected")) {
            days.push(child.value)
        }
    }
    const args = {
            name: document.getElementById("name").value,
            link: document.getElementById("link").value, time: `${hour}:${minute}`,
            repeats: document.getElementById("select").value, days: days,
            starts: parseInt(document.getElementById("starts_select").value)*days.length,
            text: document.getElementById("text_select").value,
            id: parameter, email: global_username
        }
    if (document.getElementById("password").value.length > 0) {args['password'] = document.getElementById("password").value}
    const payload = {
        headers: {'Content-Type': 'application/json'},
        method: 'POST',
        body: JSON.stringify(args)
    }
    const url = parameter === 'register' ? '/register' : '/update'
    if (!document.getElementById("name").value || !document.getElementById("link").value || days.length === 0) {
        created = false
        enableButton('submit')
    }
    if (!document.getElementById("name").value) {return document.getElementById("error").innerText = "Please provide a name for your meeting"}
    if (!document.getElementById("link").value) {return document.getElementById("error").innerText = "Please provide a link for your meeting"}
    if (days.length === 0) {return document.getElementById("error").innerText = "Please provide days for your meeting."}
    await fetch(url, payload)
    await skipTutorial()
}

async function logOut() {
    document.cookie = "email=; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
    await fetch(`/logout?email=${global_username}&session_id=${document.cookie.match('(^|;)\\s*session_id\\s*=\\s*([^;]+)')?.pop() || ''}`);
    document.cookie = "session_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
    location.replace('/login')
}


function browser() {
    if (navigator.userAgent.indexOf("Chrome") > -1) {}
        else if (navigator.userAgent.indexOf("Firefox") > -1) {
            document.getElementById(`tutorial0`).children[0].innerText =
                "You should see a gray bar indicating that popups are blocked. " +
                "Click on the box on the right that says Preferences and allow popups. " +
                "If you don't see a gray bar, you should see an icon on the left side of your search bar. Click this " +
                "to enable popups."
        }
        else if (navigator.userAgent.indexOf("Safari") > -1) {
            document.getElementById(`tutorial0`).children[0].innerText =
                "Your popups are not enabled. Click ⌘ , to get to browser settings. " +
                "Click on the websites tab at the top, and scroll down to the bottom where it says Pop-up Windows. " +
                "On the right, you should see the text 'linkjoin.xyz' with a select menu to its right. Click on that menu and select 'allow'."
        }
}


async function popupWarn(item, skip) {
    tutorial_active = true
    item = parseInt(item)
    if (document.getElementById("blur").style.opacity !== "0.4") {
        blur(true)
    }
    if (item === 0) {
        browser()
        document.getElementById("check_popup").style.display = "flex"
        document.getElementById(`tutorial-1`).style.display = "none"
        await sleep(5000)
        let newWindow = window.open()
        if (newWindow) {
            document.getElementById(`tutorial1`).style.display = "flex"
            await fetch(`/tutorial`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({'email': global_username, 'step': 1})
            })
            document.getElementById("check_popup").style.display = "none"
            return newWindow.close()
        }
        await fetch(`/tutorial`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({'email': global_username, 'step': 0})
        })
        document.getElementById(`tutorial0`).style.display = "flex"
        return document.getElementById("check_popup").style.display = "none"
    }
    else if (item === 1) {
        if (skip) {
            document.getElementById("popups_not_enabled").style.display = "none"
            document.getElementById("tutorial1").style.display = "flex"
            return document.getElementById("check_popup").style.display = "none"
        }
        browser()
        document.getElementById("check_popup").style.display = "flex"
        document.getElementById(`tutorial0`).style.display = "none"
        document.getElementById(`tutorial-1`).style.display = "none"
        document.getElementById(`popups_not_enabled`).style.display = "none"
        await sleep(5000)
        document.getElementById("check_popup").style.display = "none"
        let newWindow = window.open()
        if (newWindow) {newWindow.close()}
        else {return document.getElementById("popups_not_enabled").style.display = "flex"}
        document.getElementById("tutorial1").style.display = "flex"
    }
    document.getElementById("add_number_div").style.display = "none"
    try {document.getElementById(`tutorial${item}`).style.display = "flex"}
    catch {}
    try {document.getElementById(`tutorial${parseInt(item)-1}`).style.display = "none"}
    catch {}
}


async function refresh(id="insert") {
    let insert = document.getElementById(id)
    while (insert.firstChild) {insert.removeChild(insert.firstChild)}
}

async function addNumberShow() {
    const content = document.getElementById('add_number_div').children[1]
    if (number === "None") {
        content.children[0].innerText = 'Add phone number'
        content.children[1].innerText = "We noticed that you haven't added a phone number to your account. This means that you won't receive text reminders for your links. To add a number, type it in below. If you don't want to add your number, click the arrow in the upper left."
        content.children[3].innerText = 'Add Number'
    }
    else {
        content.children[0].innerText = 'Change phone number'
        content.children[1].innerText = "To change the phone number for your text reminders, type it in below and click 'Change Number'."
        content.children[3].innerText = 'Change Number'
    }
    document.getElementById('add_number_div').style.display = 'flex'
    blur(true)
}

async function add_number(id) {
    let country = await fetch('https://linkjoin.xyz/location').then(response => response.json())
    const countryCode = countryCodes[country['country']]
    let number = document.getElementById(id).value
    await fetch('/add_number',
        {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({
                'email': global_username,
                'countrycode': countryCode['code'],
                'number': number})}
    )
    document.getElementById("add_number_div").style.display = "none"
    blur(false)
    if (id === 'number') {
        hide('add_number_div')
    }
    else {
        hide('settings')
    }

}

async function no_add_number() {
    if (number === "None") {number = ''}
    await fetch('/add_number',
        {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({
                'email': global_username,
                'countrycode': '',
                'number': number})}
    )
    document.getElementById("add_number_div").style.display = "none"
    blur(false)
}

async function checkTutorial() {
    const tutorial_completed = await fetch('/tutorial_complete',
        {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({email: global_username})})
        .then(response => response.json())
    if (tutorial_completed['tutorial'] === "done" && number === "None" && window.innerWidth >= 1000) {
        document.getElementById("add_number_div").style.display = "block"
        blur(true)
    }
}

async function skipTutorial() {
    await fetch(`/tutorial`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({'email': global_username, 'step': 'done'})
    })
    location.reload()
}

document.addEventListener("click", (e) => {
    if (e.target.id !== "hamburger_dropdown" && e.target.id !== "hamburger" &&
        !document.getElementById("hamburger").contains(e.target)) {
        document.getElementById("hamburger_dropdown").classList.remove("expand")
        document.getElementById("hamburger").classList.remove("expand")
    }

})

document.addEventListener("click", event => {if(event.target.matches("#days button")) event.target.classList.toggle("selected")})

function pageSetup() {
    document.getElementById('notes_div').addEventListener('click', unRenderNotes)
    document.getElementById('notes_textarea').addEventListener('focusout', renderNotes)
    document.getElementById('notes_textarea').addEventListener('change', saveNotes)
    Array.from(document.getElementsByClassName('popup-time')).forEach((e, index, arr) =>
    {e.addEventListener('keypress', i => {
        if (index === 0) {
            if (parseInt(i.key) > 1 || parseInt(e.value.length) === 1) {
                e.value += i.key
                arr[2].focus()
                i.preventDefault()
            }
             if (!i.code.includes('Digit') || e.value.length > 1 || (e.value.length === 1 && (parseInt(e.value) > 1 || parseInt(i.key) > 2))) {
                i.preventDefault()
             }
             if (parseInt(e.value) > 12) {
                 e.value = e.value.slice(0, -1)
             }
        }
        else if (index === 2) {
            if (!i.code.includes('Digit') || e.value.length > 1 || (e.value.length === 1 && parseInt(e.value) > 5)) {
                i.preventDefault()
             }
        }
    })})
    document.getElementsByClassName('popup-time')[0].addEventListener('blur', e => {
        if (e.target.value.length === 1) {
            e.target.style.width = '10px'
        }
    })
    document.getElementsByClassName('popup-time')[0].addEventListener('focus', e => e.target.style.width = '20px')
    document.getElementsByClassName('popup-time')[2].addEventListener('blur', e => {
        if (e.target.value.length === 1) {
            e.target.value = '0' + e.target.value
        }
    })
}

function openTutorial() {
    document.getElementById('tutorial').classList.toggle('open')
    if (document.getElementById('open-tutorial') !== null) {
        document.getElementById('open-tutorial').classList.toggle('open')
    }

}

function closeTutorial() {
    document.getElementById('tutorial').classList.remove('open')
    if (document.getElementById('open-tutorial') !== null) {
        document.getElementById('open-tutorial').classList.remove('open')
    }
}

async function tutorialFinished() {
    await fetch('/tutorial_changed', {headers: {email: global_username, finished: 'true'}})
    location.reload()
}

async function sendNotif(text, color) {
    const notif = document.getElementById('notif')
    if (notif.style.zIndex === "2") {return}
    notif.style.zIndex = "2"
    notif.style.borderLeftColor = color
    notif.innerText = text
    for (let i = 0; i < 1; i += 0.01) {
        notif.style.opacity = (i).toString()
        await sleep(3)
    }
    await sleep(5000)
    for (let i = 1; i > 0; i -= 0.01) {
        notif.style.opacity = (notif.style.opacity-0.01).toString()
        await sleep(3)
    }
    notif.style.zIndex = "-1"
}

async function showTutorial(checked) {
    if (checked) {
        await fetch('/tutorial_changed', {headers: {email: global_username, finished: 'false'}})
    }
    else {
        await fetch('/tutorial_changed', {headers: {email: global_username, finished: 'true'}})
    }
    location.reload()
}


function openSettings() {
    document.getElementById('settings').style.display = 'flex'
    blur(true)
}


async function openEarly() {
    await fetch('/open_early', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: global_username, open: document.getElementById('settings-open-early').value})
    })
}


async function resetPassword() {
    document.getElementById('settings-reset-password').innerText = 'Sent!'
    await fetch('/reset-password', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({'token': token, 'email': global_username})
    })
    await sleep(3000)
    document.getElementById('settings-reset-password').innerText = 'Send'
}


async function openDeletedLinks() {
    hide('settings')
    blur(true)
    await load_links(global_username, global_sort, "deleted-links")
    document.getElementById('deleted-links').style.display = 'flex'
}


function dropDown(el) {
    const dropdownMenu = document.createElement('div')
    dropdownMenu.classList.add('dropdown-menu')
    dropdownMenu.style.left = getOffset(el).left.toString()
    dropdownMenu.style.top = getOffset(el).top.toString()
    dropdownMenu.append(...el.children)

}