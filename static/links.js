let global_username, global_sort, tutorial_complete
let tutorial_active = false;
let created = false;
const notesInfo = {}

function blur(show) {
    const blurElement = document.getElementById("blur")
    if (show) {
        blurElement.style.opacity = "0.4"
        blurElement.style.zIndex = "3"
    }
    else {
        blurElement.style.zIndex = "-3"
        blurElement.style.opacity = "0"
    }
}

const buildUrl = (base, ...queryParams) => {
    const url = new URL(base, document.location.href);
    for (const [name, value] of queryParams)
      url.searchParams.append(name, `${value}`);
    return url.toString();
}

async function db(username) {
    if (await fetch('/db', {headers: {'email': username}}).then(response => response.text()) === 'Not logged in') {
        return location.replace('/login?error=not_logged_in')
    }
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
    await tutorial(4)
}

function hide(popup) {
    document.getElementById(popup).style.display = "none"
    blur(false)
}

function edit(link) {
    const element = document.getElementById("popup")
    element.style.display = "flex"
    blur(true)
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
    document.getElementById("share_link").value = link['share']
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
    navigator.clipboard.writeText(link).then(async () => {
        document.getElementById(id).innerText = "Copied!"
        await sleep(2000)
        document.getElementById(id).innerText = "Copy link"
    })
}

async function load_links(username, sort) {
    const cookieSessionId = document.cookie.match('(^|;)\\s*session_id\\s*=\\s*([^;]+)')?.pop() || ''
    const sessionId = await fetch('/get_session', {headers: {'email': username}}).then(id => id.json())
    if (sessionId === null) {location.replace('/login?error=not_logged_in')}
    else if (cookieSessionId !== sessionId['session_id']) {location.replace('/login?error=not_logged_in')}
    global_username = username
    global_sort = sort
    let link_events = []
    const insert = document.getElementById("insert")
    for (let i=0; i<3; i++) {
        const placeHolder = document.createElement("div")
        placeHolder.classList.add("placeholder")
        insert.appendChild(placeHolder)
    }
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
            if (link['active'] === "false") {
                linkOpacity = 0.6
                nameContainerOpacity = 0.7
                checkboxChecked = false
            }
            const parameterLink = JSON.stringify(link).replaceAll('"', "'")
            const link_event = `<div class="link_event" id="${iterator}" style="opacity: ${link['active'] === 'false' ? 0.6 : 1}">
                <div class="time">${linkTime}</div>
                <div style="cursor: pointer; opacity: ${nameContainerOpacity}" onclick="window.open('${link['link']}')">
                    <div class="link_event_title" style="color: ${link['active'] === 'true' ? '#2B8FD8' : '#B7C0C7'}">${link['name']}</div>
                    <div class="join_now">Click to join the room now</div>
                </div>
                <div class="days">${link['days'].join(", ")}</div>
                <div class="menu" style="height: ${menuHeight}" id="menu${iterator}">
                    <div onclick="edit(${parameterLink})">Edit</div>
                    <hr class="menu_line"> 
                    <div onclick="delete_(${parameterLink})">Delete</div>
                    <hr class="menu_line">
                    <div onclick="share(${parameterLink})">Share</div>
                    <hr class="menu_line">
                    <div onclick="createNote('${link['name']}', '${link['id']}')">Notes</div>
                    <hr class="menu_line">
                    <div id="copylink${link['id']}" onclick="copyLink('${link['link']}', 'copylink${link['id']}')">Copy link</div>
                    ${password}
                </div>
                <input class="checkbox" id="toggle${iterator}" type="checkbox">
                <label class="switch" id="for${iterator}" for="toggle${iterator}" onclick="disable(${parameterLink}, '${username}')"></label>
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
        })
        for (const [index, Checked] of checked.entries()) {
            if (Checked) {
                document.getElementById('toggle'+index).checked = 'checked'
            }

        }
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

    if (tutorial_completed['tutorial'] !== "done" && window.innerWidth >= 1000) {await tutorial(tutorial_completed['tutorial'])}
    await check_day(username)
    //await sleep(200)
    await checkTutorial()
    clearInterval(open)
    start(username, links, sort)
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
    location.replace("/sort?sort="+document.getElementById("sort").value.toString())
}


async function register_link(parameter) {
    if (created) {return}
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
    skipTutorial()
    hide('popup')
    await fetch(url, args)
    location.reload()
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


async function tutorial(item, skip) {
    tutorial_active = true
    item = parseInt(item)
    if (document.getElementById("blur").style.opacity !== "0.4") {
        blur(true)
        if (item >= 4) {await popUp('popup')}
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
            document.getElementById("box").style.zIndex = "5"
            document.getElementById("box").style.background = "rgba(255, 255, 255, 0.1)"
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
        document.getElementById("box").style.zIndex = "5"
        document.getElementById("box").style.background = "rgba(255, 255, 255, 0.1)"
    }
    else if (item === 2) {
        document.getElementById("box").style.zIndex = "auto"
        document.getElementById("box").style.background = null
        document.getElementById("links_menu").style.zIndex = "5"
        document.getElementById("links_menu").style.background = "rgba(255, 255, 255, 0.2)"
    }
    else if (item === 3) {
        document.getElementById("links_menu").style.zIndex = "auto"
        document.getElementById("links_menu").style.background = null
        document.getElementById("plus_button").style.background = "rgba(255, 255, 255, 0.2)"
        document.getElementById("plus_button").style.zIndex = "5"
    }
    else if (item === 4) {
        if (document.getElementById("tutorial3").style.display !== "flex") {return}
        if (document.getElementById("popup").style.display !== "flex") { popUp('popup')}
        document.getElementById("plus_button").style.zIndex = "auto"
        document.getElementById("plus_button").style.background = null
    }
    else if (item === 6) {
        document.getElementById("select").style.background = "rgba(255, 255, 255, 0.2)"
        document.getElementById("select").style.borderRadius = "5px"
    }
    else if (item === 7) {
        document.getElementById("select").style.background = null
        document.getElementById("starts_select").style.background = "rgba(255, 255, 255, 0.2)"
        document.getElementById("starts_select").style.borderRadius = "5px"
        document.getElementById("starts_select").style.padding = "5px"
        document.getElementById("tutorial9").style.boxShadow = "-6px 16px 18px black;"
    }
    else if (item === 8) {
        document.getElementById("starts_select").style.background = null
        document.getElementById("starts_select").style.borderRadius = null
        document.getElementById("days").style.background = "rgba(255, 255, 255, 0.2)"
    }
    else if (item === 9) {
        document.getElementById("days").style.background = null
        document.getElementById("text_select").style.background = "rgba(255, 255, 255, 0.2)"
        document.getElementById("text_select").style.borderRadius = "5px"
        document.getElementById("text_select").style.paddingLeft = "5px"
    }
    else if (item === 10) {
        document.getElementById("text_select").style.background = null
        document.getElementById("text_select").style.borderRadius = null
        document.getElementById("text_select").style.paddingLeft = null
    }
    if (item === 11) {
        document.getElementById("tutorial9").style.display = "none"
        await fetch(`/tutorial`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({'email': global_username, 'step': 'done'})
        })
        tutorial_complete = true
    }
    else {
        await fetch(`/tutorial`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({'email': global_username, 'step': item})
        })
    }
    document.getElementById("add_number_div").style.display = "none"
    try {document.getElementById(`tutorial${item}`).style.display = "flex"}
    catch {}
    try {document.getElementById(`tutorial${parseInt(item)-1}`).style.display = "none"}
    catch {}
}

async function skipTutorial() {
    return await fetch(`/tutorial`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({'email': global_username, 'step': 'done'})
    })
}


async function refresh() {
    let insert = document.getElementById("insert")
    while (insert.firstChild) {insert.removeChild(insert.firstChild)}
}



async function add_number() {
    let country = await fetch('https://linkjoin.xyz/location').then(response => response.json())
    const countryCode = countryCodes[country['country']]
    let number = document.getElementById("number").value
    await fetch('/add_number',
        {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({
                'email': global_username,
                'countrycode': countryCode['code'],
                'number': number})}
    )
    document.getElementById("add_number_div").style.display = "none"
    blur(false)
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

// TODO: Add notes feature where in the dot menu for each link, you can add notes.
// TODO: Store all notes for links (deleted or not) in menu below sort by, where you can click and there's a
// TODO: Paginator and search bar for your meeting notes, as well as an option to delete the note.

async function checkTutorial() {
    const tutorial_completed = await fetch('/tutorial_complete',
        {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({email: global_username})})
        .then(response => response.json())
    if (tutorial_completed['tutorial'] === "done" && number === "None" && window.innerWidth >= 1000) {
        document.getElementById("add_number_div").style.display = "block"
        blur(true)
    }
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

document.addEventListener("click", (e) => {
    if (e.target.id !== "hamburger_dropdown" && e.target.id !== "hamburger" &&
        !document.getElementById("hamburger").contains(e.target)) {
        document.getElementById("hamburger_dropdown").classList.remove("expand")
        document.getElementById("hamburger").classList.remove("expand")
    }

})

document.addEventListener("click", event => {if(event.target.matches("#days button")) event.target.classList.toggle("selected")})

async function showNotes(changing) {
    const notes = await fetch('/notes', {headers: {'email': global_username}}).then(r => r.json())
    if (notes.length !== 0) {
        if (changing !== true) {
            notesInfo['index'] = 0
        }
        if (notesInfo['notes'] === undefined) {
            notesInfo['notes'] = notes
        }
        await popUp('popup_notes')
        notesInfo['id'] = notesInfo['notes'][notesInfo['index']]['id']
        notesInfo['name'] = notesInfo['notes'][notesInfo['index']]['name']
        document.getElementById('popup_notes').children[2].innerText = `Meeting notes for ${notesInfo['notes'][notesInfo['index']]['name']}`
        const html = await fetch('/markdown_to_html',
        {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({markdown: notesInfo['notes'][notesInfo['index']]['markdown']})}).then(r => r.text())
        document.getElementById('notes_div').innerHTML = html
    }
    else {
        await sendNotif('You do not have any meeting notes. Try creating some from the dot menus of your links!', '#ba1a1a')
    }


}

function pageSetup() {
    document.getElementById('notes_div').addEventListener('click', unRenderNotes)
    document.getElementById('notes_textarea').addEventListener('focusout', renderNotes)
    document.getElementById('notes_textarea').addEventListener('change', saveNotes)

}

async function renderNotes() {
    const html = await fetch('/markdown_to_html',
        {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({markdown: document.getElementById('notes_textarea').value})}).then(r => r.text())
    const divNotes = document.getElementById('notes_div')
    divNotes.innerHTML = html
    divNotes.style.display = 'block'
    document.getElementById('notes_textarea').style.display = 'none'
}

async function unRenderNotes() {
    if (document.activeElement === document.getElementById('notes_textarea')) {return}
    document.getElementById('notes_div').style.display = 'none'
    document.getElementById('notes_textarea').style.display = 'block'
    notesInfo['notes'].forEach(i => {
        if (i['name'] === notesInfo['name'] && i['id'] === notesInfo['id']) {
            document.getElementById('notes_textarea').value = i['markdown']
        }
    })
    document.getElementById('notes_textarea').focus()
}

async function saveNotes() {
    await fetch('/notes', {method: 'POST', headers: {'Content-Type': 'application/json', email: global_username},
        body: JSON.stringify({
            id: notesInfo['id'],
            name: notesInfo['name'],
            date: new Date().toLocaleString('en-us',{month:'long', year:'numeric', day: 'numeric'}),
            markdown: document.getElementById('notes_textarea').value
        })})
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


async function createNote(name, id) {
    const notes = await fetch('/notes', {headers: {'email': global_username}}).then(r => r.json())
    let found = false
    notes.forEach((i, index) => {
        if (i['name'] === name && i['id'] === parseInt(id)) {
            notesInfo['name'] = name
            notesInfo['id'] = parseInt(id)
            notesInfo['index'] = index
            showNotes(true)
            found = true
        }
    })
    if (found) {return}
    await fetch('/notes', {method: 'POST', headers: {'Content-Type': 'application/json', email: global_username},
        body: JSON.stringify({
            id: parseInt(id),
            name: name,
            markdown: '',
            date: new Date().toLocaleString('en-us',{month:'long', year:'numeric', day: 'numeric'}),
        })})
    notesInfo['name'] = name
    notesInfo['id'] = parseInt(id)
    notesInfo['index'] = notes.length
    await showNotes(true)
}


async function notesNext(direction) {
    if (direction === 'next') {
        notesInfo['index'] !== notesInfo['notes'].length-1 ? notesInfo['index']++ : null
    }
    else {
        notesInfo['index'] !== 0 ? notesInfo['index']-- : null
    }
    await showNotes(true)
}


async function searchNotes(content) {
    const notes = await fetch('/notes', {headers: {'email': global_username}}).then(r => r.json())
    const newNotes = []
    notes.forEach(i => {
        if (i['name'].toLowerCase().includes(content) || i['date'].toLowerCase().includes(content)) {
            newNotes.push(i)
        }
    })
    notesInfo['notes'] = newNotes
    notesInfo['index'] = 0
    await showNotes(true)
}