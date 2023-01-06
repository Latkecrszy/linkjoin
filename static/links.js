let global_username, global_sort, tutorial_complete, global_links, webSocket, defaultPopup
let timeOffPage = 0
let tutorial_active = false;
let connected = true;

const notesInfo = {}


window.addEventListener('offline', () => {connected = false; console.log('disconnected')})
window.addEventListener('online', async () => {
    console.log('reconnected');
    location.reload()
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
                console.log(el.style)
            }
        } else if (key === 'attrs') {
            for (const [name, attr] of Object.entries(value)) {
                el.setAttribute(name, attr)
            }
        }
    }

    return el
}

function addZeroes(e) {
    if (e.includes('/')) {
        return e.split('/').map(i => {
            if (i.toString().length === 1) {
                return `0${i}`
            }
            return i
        }).join('/')
    }
    else {
        return `0${e}`
    }

}

function openMenu(el) {
    el.children[el.children.length-1].style.display = 'flex';
}

function blur(show) {
    document.getElementById("blur").style.opacity = show ? "1" : "0"
    document.getElementById("blur").style.background = show ? "rgba(0, 0, 0, 0.4)" : "0"
    document.getElementById("blur").style.zIndex = show ? "3" : "-3"
}

function getOffset(el) {
    const rect = el.getBoundingClientRect();
    return {
        left: rect.left + window.scrollX,
        top: rect.top + window.scrollY
    }
}


async function popUp(popup) {
    if (confirmed === 'false') {
        if (popup === 'popup') {
            return await sendNotif(`Before you make your first link, please check your inbox for ${global_username} to confirm your email address.`, '#ba1a1a')
        }
        return await sendNotif(`Check your inbox for ${global_username} to confirm your email address.`, '#ba1a1a')
    }
    if (defaultPopup) {
        hide('popup')
    }
    document.getElementById(popup).classList.add('active')
    document.getElementById(popup).classList.remove('invisible')
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
    document.getElementById(popup).classList.add('invisible')
    document.getElementById(popup).classList.remove('active')
    blur(showBlur)
    if (popup === 'popup') {
        enableButton('submit')
        document.getElementById(popup).innerHTML = defaultPopup
        Array.from(document.getElementsByClassName('popup-time')).forEach(timeListener)
    }
}

function edit(link) {
    document.getElementById('popup').classList.add('active')
    document.getElementById('popup').classList.remove('invisible')
    blur(true)
    if (link === 'tutorial') {
        document.getElementById("title").innerText = "Edit your meeting";
        document.getElementById("submit").innerHTML = `Update <img src="/static/images/right-angle.svg" alt="right arrow">`
        document.getElementById("name").value = 'Tutorial Link'
        document.getElementById("link").value = 'https://linkjoin.xyz';
        document.getElementById("am").selected = "selected";
        document.getElementById("hour").value = 1;
        document.getElementById("minute").value = "00";
        ['Mon', 'Tue'].forEach(day => document.getElementById(day).classList.add("selected"))
        return document.getElementById("submit").setAttribute('onClick', "registerLink('tutorial')")
    }
    document.getElementById("name").value = link["name"]
    document.getElementById("link").value = link["link"]
    document.getElementById("text_select").value = link["text"].toString()
    if (link['date']) {
        changeDateSelect()
        let date = new Date(link['date']).toLocaleDateString()
        document.getElementById("date-select").value = addZeroes(date)
    }

    if ("password" in link) {document.getElementById("password").value = link["password"]}
    else {document.getElementById("password").value = null}
    if (parseInt(link['time'].split(":")[0]) === 12) {
        document.getElementById("am").innerText = 'PM'
        document.getElementById("hour").value = 12
    }
    else if (parseInt(link['time'].split(":")[0]) === 0) {document.getElementById("hour").value = 12}
    else if (parseInt(link['time'].split(":")[0]) > 12) {
        document.getElementById("hour").value = parseInt(link['time'].split(":")[0])-12
        document.getElementById("am").innerText = 'PM'
    }
    else {
        document.getElementById("hour").value = parseInt(link['time'].split(":")[0])
    }
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
    const deleteButton = document.getElementById("delete_button")
    window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
    document.getElementById("popup-delete").style.display = "flex"
    document.getElementById("popup-delete").classList.remove('invisible')
    document.getElementById("popup-delete").classList.add('active')
    if (link === 'tutorial') {
        document.getElementById("popup-delete").children[0].innerHTML = 'Are you sure you want to delete <b>Tutorial</b>?'
        return deleteButton.addEventListener('click', () => {location.reload()})
    }
    document.getElementById("popup-delete").children[0].innerHTML = 'Are you sure you want to delete <b>'+link['name']+'</b>?'
    const newButton = deleteButton.cloneNode(true)
    deleteButton.parentNode.replaceChild(newButton, deleteButton)
    newButton.addEventListener('click', async () => {
        hide('popup-delete')
        await fetch('/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: link['id'], email: link['username']})
        })
        if ((global_links['links']).length === 0) {return location.reload()}
    })
    blur(true)
}

function share(link, link_el) {
    document.getElementById("popup-share").style.zIndex = "11"
    document.getElementById("popup-share").classList.remove('invisible')
    document.getElementById("popup-share").classList.add('active')
    document.getElementById("popup-share").style.display = {"none": "flex", "flex": "none"}[document.getElementById("popup-share").style.display]
    // document.getElementById("share_link").value = link === 'tutorial' ? 'https://linkjoin.xyz/addlink?id=tutorial' : link['share']
    let demoLink = document.getElementById('popup-share-demo-link')
    if (demoLink.firstChild) {demoLink.removeChild(demoLink.firstChild)}
    demoLink.appendChild(link_el.cloneNode(true))
    demoLink.children[0].classList.remove('expanded')
    demoLink.children[0].removeChild(demoLink.children[0].getElementsByClassName('switch-checkbox')[0])
    demoLink.children[0].removeChild(demoLink.children[0].getElementsByClassName('switch')[0])
    demoLink.children[0].removeChild(demoLink.children[0].getElementsByClassName('dot-menu')[0])
    console.log(link)
    document.getElementById('popup-share-button').onclick = () => {shareLink(link)}
    blur(true)
    window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
}

async function disable(link) {
    await fetch('/disable', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: link['username'], id: link['id']})
    })
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
    document.getElementById("popup-delete").style.display = "flex"
    document.getElementById("popup-delete").children[0].innerHTML = 'Are you sure you want to permanently delete <b>'+link['name']+'</b>? This action cannot be undone.'
    document.getElementById("delete_button").addEventListener('click', async () => {
        hide('popup-delete')
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


function createLink(link, id="insert", iterator=0) {
    let hour = link["time"].split(":")[0]
    let meridian = "am"
    if (parseInt(hour) === 12) {meridian = "pm"}
    else if (parseInt(hour) === 0) {hour = 12}
    else if (parseInt(hour) > 12) {hour = parseInt(hour) - 12; meridian = "pm"}
    const time = `${hour}:${link["time"].split(":")[1]} ${meridian}`
    let link_event;

    link_event = createElement('div', ['link'])
    if (link['active'] === 'false' && id === 'insert') {
        link_event.classList.add('link-disabled')
    }
    if (id === 'pending-links') {
        link_event.classList.add('pending-link')
    }
    link_event.appendChild(createElement('p', ['time'], '', time))
    const joinMeeting = createElement('div', ['join-meeting'], '', '',
        {'events': {'onclick': () => {window.open(link['link'])}}})
    joinMeeting.appendChild(createElement('p', ['name'], '', link['name']))
    joinMeeting.appendChild(createElement('p', ['description'], '', 'Click to join the meeting now'))
    link_event.appendChild(joinMeeting)
    let linkDaysValue = link['days'].join(", ")
    if ('date' in link && link['date'] !== '') {
        linkDaysValue += ' - ' + new Date(link['date']).toLocaleDateString()
    }
    link_event.appendChild(createElement('p', ['days'], '', linkDaysValue))
    if (id === "insert") {
        link_event.appendChild(createElement('input', ['switch-checkbox'], `switch${iterator}`,
            '', {'attrs': {'type': 'checkbox'}}))
        link_event.appendChild(createElement('label', ['switch'], '', '',
            {'attrs': {'for': `switch${iterator}`}, 'events': {'onclick': () => {disable(link)}}}))
    }

    link_event.appendChild(createElement('img', ['link-expand'], '', '',
        {'events': {'onclick': () => link_event.classList.toggle('expanded')},
            'attrs': {'src': 'static/images/angle-down.svg', 'alt': 'down arrow'}}))

    if (id === 'pending-links') {
        link_event.appendChild(createElement('button', ['pending-link-buttons', 'accept'], '', 'Accept',
            {'events': {'onclick': async () => {await acceptLink(link)}}}))
        link_event.appendChild(createElement('button', ['pending-link-buttons', 'decline'], '', 'Ignore',
            {'events': {'onclick': async () => {await acceptLink(link, false)}}}))
    }
    else {
        link_event.appendChild(createElement('img', ['dot-menu'], '', '',
        {'attrs': {'src': 'static/images/ellipsis.svg', 'alt': '3 dots'}, 'events': {'onclick': () => {openMenu(link_event)}}}))
        const menu = createElement('div', ['menu'])
        let buttons;
        if (id === 'insert') {
            buttons = {'Edit': () => edit(link), 'Delete': () => delete_(link), 'Share': () => share(link, link_event),
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
    }
    //TODO: Make hoverable and make links not open (actually disable them in redirect.js (or here))
    console.log('checking superdisabled')
    if (link['superDisabled']) {
        console.log('disabled better')
        link_event.classList.add('superDisabled')
        link_event.title = 'This link has been disabled by your organization administrator'
    }
    return link_event
}


function createPendingLinks(username, links) {
    const pendingLinks = createElement('div', ['pending-links'], 'pending-links')
    for (const link of links) {
        pendingLinks.appendChild(createLink(link, 'pending-links'))
    }
    pendingLinks.appendChild(createElement('hr', ['hr-pending-links'], 'hr-pending-links', ''))
    document.getElementById('insert').prepend(pendingLinks)
}


function createLinks(username, links, id="insert") {
    let final = []
    const new_links = []
    if (global_sort === "day") {
            const link_list = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": [], "Sat": [], "Sun": []}
            for (const link_info of links) {link_list[link_info['days'][0]].push(link_info)}
            for (const day in link_list) {for (let key of link_list[day]) {final.push(key)}}
        }
    else if (global_sort === "time") {
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
    else if (global_sort === "datetime") {
        let added_time = 0.0000001
        const link_dict = {"Mon": {}, "Tue": {}, "Wed": {}, "Thu": {}, "Fri": {}, "Sat": {}, "Sun": {}, "dates": {}}
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
    final.reverse()
    for (const link of final) {
        let link_event = createLink(link, id, iterator)
        checked.push(link['active'] === 'true')
        new_links.push(link_event)
        iterator += 1
    }
    if (id === 'insert') {
        document.addEventListener('click', e => {
            Array.from(document.getElementsByClassName('menu')).forEach(i => {
                if (!['Copied!', 'Password', 'Copy link'].includes(e.target.innerText) &&
                    !e.target.classList.contains('dot-menu') && !i.classList.contains('tutorial')) {
                    i.style.display = 'none'
                }
            })
        })
    }
    const insert = document.getElementById(id)
    let len = insert.children.length
    new_links.forEach(i => insert.prepend(i))
    for (let x = 0; x < len; x++) {
        insert.removeChild(insert.children[insert.children.length-1])
    }
    try {
        checked.forEach((Checked, index) => {if (Checked) {document.getElementById('switch'+index).checked = 'checked'}})
    }
    catch {}
    if (global_links['pending-links'].length > 0) {
        createPendingLinks(username, global_links['pending-links'])
    }
}

async function load_links(username, sort, id="insert") {
    if (!connected) {
        return
    }
    global_username = username
    webSocket = new WebSocket(`ws://127.0.0.1:8000/database_ws?email=${encodeURIComponent(username)}`)
    webSocket.onopen = () => {
        webSocket.send(JSON.stringify({'email': username}))
    }
    webSocket.onmessage = async (e) => {
        let links = JSON.parse(e.data)
        for (const linkCategory of Object.values(links)) {
            linkCategory.forEach(link => {
                let newInfo = toUTC(link['days'], parseInt(link['time'].split(':')[0]),
                    parseInt(link['time'].split(':')[1]), true)
                if (newInfo['minute'] < 10) {
                    newInfo['minute'] = `0${newInfo['minute']}`
                }
                link['days'] = newInfo['days']
                link['time'] = `${newInfo['hour']}:${newInfo['minute']}`
                link['superDisabled'] = org_disabled === 'true';
            })
        }
        if (((global_links !== undefined && global_links['links'].length === 0) && links['links'].length === 1) ||
            (global_links !== undefined && global_links['links'].length === 1 && links['links'].length === 0)) {
            location.reload()
            return
        }
        global_links = links
        if (links['links'].length === 0 && !insert.classList.contains('empty')) {
            location.reload()
        }
        await createLinks(username, links['links'], 'insert')
    }
    webSocket.onclose = () => {
        connected = false
    }
    webSocket.onerror = (e) => {
        console.log(e)
    }
    let links
    global_sort = sort
    try {
        document.getElementById(id).style.display = 'flex'
    }
    catch {
        while (!connected) {
            await sleep(5000)
        }
        await refresh()
        await load_links(username, global_sort)
    }
    while (global_links === undefined) {
        await sleep(500)
    }

    if (id === "insert") {
        links = global_links['links']
    }
    else {
        links = global_links['deleted-links']
    }
    id = id === 'deleted-links' ? 'deleted-links-body' : id
    const insert = document.getElementById(id)
    if (id !== 'insert') {
        blur(true)
    }
    if (links.toString() === '' && id === 'insert' && global_links['pending-links'].length === 0) {
        await refresh(id)
        document.getElementById("header-links").style.margin = "0 0 0 0"
        document.getElementById("disappear").classList.remove("gone")
    }
    else if (links.toString() === '' && id !== 'insert') {
        insert.classList.add('empty')
        insert.innerHTML = `<h2>After you delete a link, it will show up here.</h2>
                            <img src="/static/images/trash.svg" alt="trash can">`
        return
    }
    else {
        await createLinks(username, links, id)
    }

    let tutorial_completed = await fetch('/tutorial_complete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email: username})})
    tutorial_completed = await tutorial_completed.json()
    if (tutorial_completed['tutorial'] !== "done") {await popupWarn(tutorial_completed['tutorial'])}
    await check_day(username)
    await checkTutorial()
    clearInterval(openInterval)
    defaultPopup = document.getElementById('popup').innerHTML
    if (error === 'link_not_found') {
        history.pushState('data', 'LinkJoin', '/links')
        await sendNotif('The link you are trying to add could not be found. Please contact the owner of this link for more information.', '#ba1a1a')
    }
    if (document.getElementsByClassName('highlight').length > 0) {
        document.getElementsByClassName('highlight')[0].scrollIntoView(true)
        await sleep(3000)
        document.getElementsByClassName('highlight')[0].style.background = 'none'
    }
    await start(username, links, sort)
}

async function check_day(username) {
    let date = new Date()
    let day = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[date.getDay()]
    let children = document.getElementById("days").children
    if (global_links['links'].length <= 3) {
        for (let child of children) {
            if (child.value === day) {child.classList.add("selected")}
        }
    }
}

async function sort() {
    location.replace("/sort?sort="+document.getElementsByClassName("sort")[0].value.toString())
}


function toUTC(days, hour, minute, opp=false) {
    const referenceDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    if (opp) {
        hour = parseInt(hour) - parseInt(new Date().getTimezoneOffset())/60
    } else {
         hour = parseInt(hour) + parseInt(new Date().getTimezoneOffset())/60
    }
    if (Math.round(hour) !== hour) {
        minute = Math.abs(Math.round(hour) - hour)*60 + parseInt(minute)
    }
    if (minute >= 60) {
        minute -= 60
        hour += 1
    }
    if (hour >= 24) {
        hour -= 24
        days = days.map(day => referenceDays[(referenceDays.indexOf(day)+1) % 7])
    }
    if (hour < 0) {
        hour += 24
        days = days.map(day => referenceDays[(referenceDays.indexOf(day)+6) % 7])
    }
    return {hour: hour, minute: minute, days: days}
}


async function registerLink(parameter) {
    disableButton(document.getElementById('submit'))
    if (parameter === 'tutorial') {location.reload()}
    let hour = parseInt(document.getElementById("hour").value || document.getElementById("hour").placeholder)
    let minute = parseInt(document.getElementById("minute").value || document.getElementById("minute").placeholder)
    if (minute.toString().length === 1) {minute = '0' + minute}
    if (document.getElementById("am").innerText === "PM" && hour !== 12) {hour += 12}
    else if (hour === 12 && document.getElementById("am").innerText === "AM") {hour += 12}
    let days = Array.from(document.getElementById("days").children).map(i => {
        if (i.classList.contains('selected')) {
            return i.value
        }
    }).filter(i => i !== undefined)
    let date = ''
    if (!document.getElementById("date-select").classList.contains('gone')) {
        date = document.getElementById('date-select').value
        let hour = new Date().getHours().toString().length === 1 ? `0${new Date().getHours().toString()}` : new Date().getHours().toString()
        let minute = new Date().getMinutes().toString().length === 1 ? `0${new Date().getMinutes().toString()}` : new Date().getMinutes().toString()
        date = new Date(
            `${date.split('/')[2]}-${date.split('/')[0]}-${date.split('/')[1]}T${hour}:${minute}`)
            .toISOString()
    }
    let UTCInfo = toUTC(days, hour, minute)
    days = UTCInfo['days']
    hour = UTCInfo['hour']
    minute = UTCInfo['minute']
    const args = {
            name: document.getElementById("name").value,
            link: document.getElementById("link").value, time: `${hour}:${minute}`,
            repeats: document.getElementById("select").value, days: days,
            date: date,
            activated: date === '',
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
        enableButton('submit')
    }
    if (!document.getElementById("name").value) {return document.getElementById("error").innerText = "Please provide a name for your meeting"}
    if (!document.getElementById("link").value) {return document.getElementById("error").innerText = "Please provide a link for your meeting"}
    if (days.length === 0) {return document.getElementById("error").innerText = "Please provide days for your meeting."}
    if (account === 'false') {
        global_links.push(args)
        localStorage.setItem('links', JSON.stringify(global_links))
    }
    else {
        await fetch(url, payload)
    }
    hide('popup')
    if (global_links['links'].length === 1) {
        location.reload()
    }
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
        document.getElementById("check-popup").style.display = "flex"
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
            document.getElementById("check-popup").style.display = "none"
            return newWindow.close()
        }
        await fetch(`/tutorial`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({'email': global_username, 'step': 0})
        })
        document.getElementById(`tutorial0`).style.display = "flex"
        return document.getElementById("check-popup").style.display = "none"
    }
    else if (item === 1) {
        if (skip) {
            document.getElementById("popups-not-enabled").style.display = "none"
            document.getElementById("tutorial1").style.display = "flex"
            return document.getElementById("check-popup").style.display = "none"
        }
        browser()
        document.getElementById("check-popup").style.display = "flex"
        document.getElementById(`tutorial0`).style.display = "none"
        document.getElementById(`tutorial-1`).style.display = "none"
        document.getElementById(`popups-not-enabled`).style.display = "none"
        await sleep(5000)
        document.getElementById("check-popup").style.display = "none"
        let newWindow = window.open()
        if (newWindow) {newWindow.close()}
        else {return document.getElementById("popups-not-enabled").style.display = "flex"}
        document.getElementById("tutorial1").style.display = "flex"
    }
    document.getElementById("add-number-div").style.display = "none"
    try {document.getElementById(`tutorial${item}`).style.display = "flex"}
    catch {}
    try {document.getElementById(`tutorial${parseInt(item)-1}`).style.display = "none"}
    catch {}
}


async function refresh(id="insert") {
    let insert = document.getElementById(id)
    if (insert) {
        while (insert.firstChild) {insert.removeChild(insert.firstChild)}
    }

}

async function addNumberShow() {
    const content = document.getElementById('add-number-div').children[1]
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
    document.getElementById('add-number-div').style.display = 'flex'
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
    document.getElementById("add-number-div").style.display = "none"
    blur(false)
    if (id === 'number') {
        hide('add-number-div')
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
    document.getElementById("add-number-div").style.display = "none"
    blur(false)
}

async function checkTutorial() {
    let tutorial_completed
    if (account === 'false') {
        tutorial_completed = {'tutorial': localStorage.getItem('tutorial_completed')}
    }
    else {
        tutorial_completed = await fetch('/tutorial_complete',
        {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({email: global_username})})
        .then(response => response.json())
    }

    if (tutorial_completed['tutorial'] === "done" && number === "None" && window.innerWidth >= 1000) {
        document.getElementById("add-number-div").style.display = "block"
        blur(true)
    }
}

async function skipTutorial(register) {
    if (document.getElementById('insert').children.length === 0) {
        location.reload()
    }
    await fetch(`/tutorial`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({'email': global_username, 'step': 'done'})
    })
    if (document.getElementById('tutorial1').style.display !== 'none') {
        location.reload()
    }
    if (register) {hide('popup')}
    await refresh()
    await load_links(global_username, global_sort)

}



document.addEventListener("click", event => {
    let date = new Date(addZeroes(document.getElementById('date-select').value.replaceAll('/', '-')))
    const day = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[date.getDay()]
    if (event.target.matches("#days button") && (document.getElementById('date-select').classList.contains('gone') ||
        event.target.value !== day)) {
        event.target.classList.toggle("selected")
    }
})

function pageSetup() {
    document.getElementById('notes_div').addEventListener('click', unRenderNotes)
    document.getElementById('notes_textarea').addEventListener('focusout', renderNotes)
    document.getElementById('notes_textarea').addEventListener('change', saveNotes)
    Array.from(document.getElementsByClassName('popup-time')).forEach(timeListener)
    document.addEventListener("click", (e) => {
        if (e.target.id !== "hamburger_dropdown" && e.target.id !== "dropdown" &&
            !document.getElementById("dropdown").contains(e.target)) {
            document.getElementById("dropdown-checkbox").checked = false
            document.getElementById("hamburger_dropdown").classList.remove("expand")
        }

        if (e.target.parentElement && !e.target.parentElement.classList.contains('demo') &&
            document.getElementById('tutorial-menu').style.display !== 'none') {
            document.getElementById('tutorial-menu').style.display = 'none'
        }
        else if (!e.target.classList.contains('menu_buttons') && e.target.id !== 'open-tutorial' && (e.target.parentElement && e.target.parentElement.id !== 'open-tutorial')) {
            closeTutorial()
        }
        if ((e.target.id !== 'open-tutorial' && !document.getElementById('tutorial').contains(e.target) &&
            e.target.id !== 'tutorial') || (e.target.parentElement.classList.value === 'menu tutorial' ||
            e.target.parentElement.parentElement.classList.value === 'menu tutorial') && e.target.innerText !== 'Copy link'){
            closeTutorial()
        }

    })

    document.getElementById('blur').addEventListener('click', () => {
        closePopup()
    })

    Array.from(document.getElementsByClassName('superDisabled')).forEach(e => {
        e.addEventListener('click', () => {
            document.getElementById('popup-org-disabled').classList.toggle('gone')
        })
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
    document.getElementById('settings').classList.remove('invisible')
    document.getElementById('settings').classList.add('active')
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
    document.getElementById('deleted-links').classList.add('active')
    document.getElementById('deleted-links').classList.remove('invisible')
}


function dropDown(el) {
    const dropdownMenu = document.createElement('div')
    dropdownMenu.classList.add('dropdown-menu')
    dropdownMenu.style.left = getOffset(el).left.toString()
    dropdownMenu.style.top = getOffset(el).top.toString()
    dropdownMenu.append(...el.children)
}


function changeDateSelect() {
    document.getElementById('starts_select').classList.toggle('gone')
    document.getElementById('date-select').classList.toggle('gone')
    document.getElementById('date-select').focus()
    document.getElementById('starts-back-arrow').classList.toggle('gone')
    document.getElementById('starts_select').children[0].selected = 'selected'
}

function checkDate(el) {
    if (el.value.split('/')[el.value.split('/').length-1].length === 4) {
        let hour = new Date().getHours().toString()
        if (hour.length === 1) {hour = `0${hour}`}
        let minute = new Date().getMinutes().toString()
        if (minute.length === 1) {minute = `0${minute}`}
        let date = new Date(
            `${el.value.split('/')[2]}-${el.value.split('/')[0]}-${el.value.split('/')[1]}T${hour}:${minute}`)
        let day = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[date.getDay()]
        document.getElementById(day).classList.add('selected')

    }
}

async function formatDate(el) {
    const monthLengths = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    el.addEventListener('keypress', e => {
        if (!(e.code.includes('Digit') || e.key === '/')) {
            e.preventDefault()
            return
        }
        let input = (el.value + e.key).split('/')
        if (input[input.length - 1] === '') {
            input.pop()
        }
        // Month:
        if (input.length === 1) {
            input = input[0]
            if (input.length === 1 && parseInt(input) > 1) {
                el.value = `0${input}/`
                e.preventDefault()
            } else if (input.length === 2 && parseInt(input) <= 12) {
                el.value += `${e.key}/`
                e.preventDefault()
            }

            if (input.length > 2) {
                e.preventDefault()
            } else if (parseInt(input) > 12) {
                e.preventDefault()
            }
        }


        else if (input.length === 2) {
            let month = input[0]
            input = input[1]
            if (input.length === 1 && parseInt(input) > 3) {
                el.value = `${month}/0${input}/`
                e.preventDefault()
            } else if (input.length === 2 && parseInt(input) <= monthLengths[parseInt(month)]) {
                el.value += `${e.key}/`
                e.preventDefault()
            }

            if (input.length > 2) {
                e.preventDefault()
            } else if (parseInt(input) > monthLengths[parseInt(month)]) {
                e.preventDefault()
            }
        }

        else if (input.length === 3) {
            if (parseInt(input[input.length-1]) === 22) {
                el.value = `${el.value.substring(0, el.value.length-2)}/202`
            }
        }
        if ((el.value+e.key)[(el.value+e.key).length-1] === (el.value+e.key)[(el.value+e.key).length-2] &&
            (el.value+e.key)[(el.value+e.key).length-1] === '/') {
            el.value = el.value.substring(0, el.value.length-1)
        }
    })
}


function timeListener(e, index, arr) {
    e.addEventListener('keypress', i => {
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
    })
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

function closePopup() {
    if (document.getElementsByClassName('active').length > 0) {
        document.getElementsByClassName('active')[0].classList.add('invisible')
        document.getElementsByClassName('active')[0].classList.remove('active')
        blur(false)
    }
}

document.addEventListener('visibilitychange', async e => {
    if ((Date.now() - timeOffPage)/1000 > 60 && document.visibilityState === 'visible') {
        location.reload()
    }
    timeOffPage = Date.now()

})


function verifyEmail(e) {
    if (e.keyCode === 13 && e.target.value !== '') {
        createShareEmail()
    }
}


function createShareEmail() {
    let input = document.getElementById('popup-share-emails-input')
    let container = document.getElementById('popup-share-emails-container')
    let color
    let textDecoration
    if (/\S+@\S+\.\S+/.test(input.value)) {
        color = ''
        textDecoration = ''
    } else {
        color = 'red'
        textDecoration = 'bold'
    }
    let newEmail = createElement('div', ['popup-share-email'], '', input.value,
            {'style': {'color': color, 'textDecoration': textDecoration}})
    newEmail.addEventListener('click', e => {removeEmail(e.target)})
    container.insertBefore(newEmail, container.children[container.children.length-1])
    input.value = ''
    input.placeholder = ''

}

function removeEmail(el) {
    let shareEmails = document.getElementById('popup-share-emails-container').children
    el.remove()
    if (shareEmails.length === 1) {
        shareEmails[0].placeholder = 'Add email'
    }
}


document.addEventListener('scroll', e => {
    console.log('start')
    document.getElementById('insert').classList.add('show')

})

const onScrollStop = callback => {
  let isScrolling;
  document.addEventListener(
    'scroll',
    e => {
      clearTimeout(isScrolling);
      isScrolling = setTimeout(() => {
        callback();
      }, 150);
    },
    false
  );
};


onScrollStop(() => {
    console.log('stopped')
  document.getElementById('insert').classList.remove('show')
});


function hidePopupEmailsInput() {
    if (document.getElementById('popup-share-emails-container').children.length >= 2) {
        document.getElementById('popup-share-emails-input').classList.add('gone')
    }
    if (document.getElementById('popup-share-emails-input').value) {
        createShareEmail()
        document.getElementById('popup-share-emails-input').classList.add('gone')
    }

}

function showPopupEmailsInput() {
    document.getElementById('popup-share-emails-input').classList.remove('gone')
    document.getElementById('popup-share-emails-input').focus()
}


function shareLink(link) {
    document.getElementById('popup-share-button').innerHTML = document.getElementById('popup-share-button').innerHTML.replace('Send', 'Sent!')
    let emails = []
    for (let i = 0; i < document.getElementById('popup-share-emails-container').children.length-1; i++) {
        if (document.getElementById('popup-share-emails-container').children[i].style.color !== 'red') {
            emails.push(document.getElementById('popup-share-emails-container').children[i].innerText)
        }
    }
    let UTCInfo = toUTC(link['days'], parseInt(link['time'].split(':')[0]), parseInt(link['time'].split(':')[1]))
    link['days'] = UTCInfo['days']
    link['time'] = `${UTCInfo['hour']}:${UTCInfo['minute']}`
    let data = {
        'email': global_username,
        'emails': emails,
        'link': link
    }
    fetch('/share-link', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(async () => {
        hide('popup-share')
        while (document.getElementById('popup-share-emails-container').children.length > 1) {
            document.getElementById('popup-share-emails-container').children[0].remove()
        }
        document.getElementById('popup-share-emails-container').children[0].placeholder = 'Add email'
    })
    .catch(error => {
        console.log(error)
    })
}


async function acceptLink(link, accept=true) {
    let data = {
        email: global_username,
        link: link,
        accept: accept
    }
    await fetch('/accept-link', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .catch(error => {
        console.log(error)
    })
}


function showPersonalSettings() {
    document.getElementById('settings-page-personal').classList.add('active')
    document.getElementById('settings-page-admin').classList.remove('active')
    document.getElementById('settings-option-personal').classList.add('selected')
    document.getElementById('settings-option-admin').classList.remove('selected')
}

function showAdminSettings() {
    document.getElementById('settings-page-personal').classList.remove('active')
    document.getElementById('settings-page-admin').classList.add('active')
    document.getElementById('settings-option-personal').classList.remove('selected')
    document.getElementById('settings-option-admin').classList.add('selected')
}


async function disableAll(checked) {
    console.log('disabling')
    await fetch('/disable-all', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({'email': global_username, 'disable': checked})
    })
    location.reload()
}
