let global_username, global_sort, tutorial_complete
let tutorial_active = false;
let created = false;
const notesInfo = {}

function blur(show) {
    document.getElementById("blur").style.opacity = show ? "0.4" : "0"
    document.getElementById("blur").style.zIndex = show ? "3" : "-3"
}

async function db(username) {
    return await fetch('/db', {headers: {'email': username}}).then(response => response.json())
}

async function popUp(popup) {
    hide('popup')
    document.getElementById(popup).style.display = "flex"
    const submit = document.getElementById("submit")
    blur(true)
    submit.innerHTML = null
    submit.innerText = "Create"
    submit.addEventListener("click", () => register_link("register"))
    document.getElementById("name").value = null
    document.getElementById("link").value = null
    document.getElementById("hour").value = 1
    document.getElementById("minute").options.selectedIndex = 0
    document.getElementById("password").value = null
    document.getElementById("title").innerText = "Schedule a new meeting"
    document.getElementById('week').selected = "selected"
    for (let child of document.getElementById("days").children) {
        if (child.value !== {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[date.getDay()]) {
            child.classList.remove("selected")
        }
    }
    document.getElementById("0").selected = "selected"
}

function hide(popup) {
    document.getElementById(popup).style.display = "none"
    blur(false)
}

function edit(link) {
    const element = document.getElementById("popup")
    element.style.display = "flex"
    blur(true)
    if (link === 'tutorial') {
        document.getElementById("submit").innerText = "Update"
        document.getElementById("name").value = 'Tutorial Link'
        document.getElementById("link").value = 'https://linkjoin.xyz';
        document.getElementById("pm").selected = "selected";
        document.getElementById("hour").value = 12;
        document.getElementById("minute").value = "00";
        ['Mon', 'Tue'].forEach(day => document.getElementById(day).classList.add("selected"))
        return document.getElementById("submit").setAttribute('onClick', "register_link('tutorial')")
    }
    document.getElementById("name").value = link["name"]
    document.getElementById("link").value = link["link"]
    document.getElementById("text_select").value = link["text"].toString()
    document.getElementById("starts_select").value = link["starts"].toString()
    if ("password" in link) {document.getElementById("password").value = link["password"]}
    else {document.getElementById("password").value = null}
    if (parseInt(link['time'].split(":")[0]) === 12) {
        document.getElementById("pm").selected = "selected"
        document.getElementById("hour").value = 12
    }
    else if (parseInt(link['time'].split(":")[0]) === 24) {document.getElementById("hour").value = 12}
    else if (parseInt(link['time'].split(":")[0]) > 12) {
        document.getElementById("hour").value = parseInt(link['time'].split(":")[0])-12
        document.getElementById("pm").selected = "selected"
    }
    else {document.getElementById("hour").value = parseInt(link['time'].split(":")[0])}
    document.getElementById("minute").value = link['time'].split(":")[1]
    document.getElementById("submit").innerText = "Update"
    document.getElementById("submit").setAttribute('onClick', `register_link(${link['id']})`)
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
        await refresh()
        await load_links(link['username'], global_sort)
    })
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

async function load_links(username, sort) {
    const cookieSessionId = document.cookie.match('(^|;)\\s*session_id\\s*=\\s*([^;]+)')?.pop() || ''
    const sessionId = await fetch('/get_session', {headers: {'email': username}}).then(id => id.json())
    if (sessionId === null || cookieSessionId !== sessionId['session_id']) {location.replace('/login?error=not_logged_in')}
    global_username = username
    global_sort = sort
    const insert = document.getElementById("insert")
    for (let i=0; i<3; i++) {insert.innerHTML += '<div class="placeholder"></div>'}
    const links = await db(username)
    if (links.toString() === '') {
        await refresh()
        document.getElementById("header_links").style.margin = "0 0 0 0"
        document.getElementById("disappear").classList.remove("gone")
    }
    else {
        document.getElementById('footer_links').style.marginTop = '100px'
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
        await refresh()
        for (const link of final) {
            const time = link["time"]
            const time_list = time.split(":")
            let pm = "am"
            if (parseInt(time_list[0]) === 12) {pm = "pm"}
            else if (parseInt(time_list[0]) === 24) {time_list[0] = 12}
            else if (parseInt(time_list[0]) > 12) {time_list[0] = parseInt(time_list[0]) - 12; pm = "pm"}
            const linkTime = time_list.join(":") + " " + pm
            let password = '';
            let menuHeight = "190px"
            if ("password" in link) {
                password = `<hr class="menu_line"><div id="${link['id'].toString()}" onclick="copyPassword('${link['id']}', '${link['password']}')">Password</div>`
                menuHeight = "235px"
            }
            let linkOpacity = 1
            let nameContainerOpacity = 1
            let checkboxChecked = true
            let switchHoverText = 'Stop your link from opening automatically'
            if (link['active'] === "false") {
                linkOpacity = 0.6
                nameContainerOpacity = 0.7
                checkboxChecked = false
                switchHoverText = 'Make your link open automatically'
            }
            let highlightDiv = highlight === link['id'].toString() ? '<div class="highlight"></div>' : ''
            const parameterLink = JSON.stringify(link).replaceAll('"', "'")
            const link_event = `<div class="link_event" id="${iterator}" style="opacity: ${link['active'] === 'false' ? 0.6 : 1}">
                ${highlightDiv}
                <div class="time">${linkTime}</div>
                <div style="cursor: pointer; opacity: ${nameContainerOpacity}" onclick="window.open('${link['link']}')">
                    <div class="link_event_title" style="color: ${link['active'] === 'true' ? '#2B8FD8' : '#B7C0C7'}">${link['name']}</div>
                    <div class="join_now">Click to join the room now</div>
                </div>
                <div class="days">${link['days'].join(", ")}</div>
                <div class="menu" style="height: ${menuHeight}" id="menu${iterator}">
                    <div onclick="edit(${parameterLink})" title="Edit your link settings">Edit</div>
                    <hr class="menu_line"> 
                    <div onclick="delete_(${parameterLink})" title="Permanently delete your link">Delete</div>
                    <hr class="menu_line">
                    <div onclick="share(${parameterLink})" title="Share your scheduled link with other people">Share</div>
                    <hr class="menu_line">
                    <div onclick="createNote('${link['name']}', '${link['id']}')" title="Take notes on your meeting">Notes</div>
                    <hr class="menu_line">
                    <div id="copylink${link['id']}" onclick="copyLink('${link['link']}', 'copylink${link['id']}')" title="Copy your meeting link">Copy link</div>
                    ${password}
                </div>
                <input class="checkbox" id="toggle${iterator}" type="checkbox">
                <label class="switch" id="for${iterator}" for="toggle${iterator}" onclick="disable(${parameterLink}, '${username}')" title="${switchHoverText}"></label>
                <img class="menu_buttons" src="static/images/ellipsis.svg" height="20" width="8" onclick="document.getElementById('menu${iterator}').style.display = 'flex'" alt="Three dots">
            </div>`
            checked.push(checkboxChecked)
            insert.innerHTML += link_event
            iterator += 1
        }
        document.addEventListener("click", (e) => {
            for (let i = 0; i < iterator; i++) {
                if (e.target.parentElement.id !== i.toString()) {
                    document.getElementById(`menu${i}`).style.display = "none"
                }
            }
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
        checked.forEach((Checked, index) => {if (Checked) {document.getElementById('toggle'+index).checked = 'checked'}})
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


async function register_link(parameter) {
    if (created) {return}
    if (parameter === 'tutorial') {location.reload()}
    created = true
    let hour = parseInt(document.getElementById("hour").value)
    const minute = document.getElementById("minute").value
    if (document.getElementById("am").value === "pm") {if (hour !== 12) {hour += 12}}
    else {if (hour === 12) {hour += 12}}
    let days = []
    for (let child of document.getElementById("days").children) {
        if (child.classList.contains("selected")) {
            days.push(child.value)
        }
    }
    const args = {
        headers: {'Content-Type': 'application/json'},
        method: 'POST',
        body: JSON.stringify({
            name: document.getElementById("name").value,
            link: document.getElementById("link").value, time: `${hour}:${minute}`,
            repeats: document.getElementById("select").value, days: days,
            starts: parseInt(document.getElementById("starts_select").value)*days.length,
            text: document.getElementById("text_select").value,
            id: parameter, email: global_username
        })
    }
    if (document.getElementById("password").value.length > 0) {args['password'] = document.getElementById("password").value}
    const url = parameter === 'register' ? '/register' : '/update'
    if (!document.getElementById("name").value) {return document.getElementById("error").innerText = "Please provide a name for your meeting"}
    if (!document.getElementById("link").value) {return document.getElementById("error").innerText = "Please provide a link for your meeting"}
    if (days.length === 0) {return document.getElementById("error").innerText = "Please provide days for your meeting."}
    await fetch(url, args)
    await skipTutorial()
}

function logOut() {document.cookie = "email=; expires=Thu, 01 Jan 1970 00:00:00 UTC;"; location.replace('/login')}


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
            document.getElementById("box").style.zIndex = "5"
            document.getElementById("box").style.background = "rgba(255, 255, 255, 0.1)"
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


async function refresh() {
    let insert = document.getElementById("insert")
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
}

function nextStep() {

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