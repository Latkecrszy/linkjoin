/*import {createElement, sendNotif, copyLink, logOut, refresh, createShareEmail, removeEmail,
    hidePopupEmailsInput, showPopupEmailsInput, verifyEmail} from "./links.js"*/
let global_username, webSocket, defaultPopup, global_bookmarks
let connected = true
var pageLoaded = false


function blur(show) {
    document.getElementById("blur").style.opacity = show ? "1" : "0"
    document.getElementById("blur").style.background = show ? "rgba(0, 0, 0, 0.4)" : "0"
    document.getElementById("blur").style.zIndex = show ? "3" : "-3"
}

async function popUp(popup) {
    if (confirmed === 'false') {
        if (popup === 'popup') {
            return await sendNotif(`Before you add a bookmark, please check your inbox for ${global_username} to confirm your email address.`, '#ba1a1a')
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
    submit.setAttribute('onClick', "registerBookmark('register')")
    document.getElementById("name").value = null
    document.getElementById("link").value = null
    document.getElementById("title").innerText = "Add a new bookmark"
}


function hide(popup, showBlur=false) {
    document.getElementById(popup).classList.add('invisible')
    document.getElementById(popup).classList.remove('active')
    blur(showBlur)
    if (popup === 'popup') {
        enableButton('submit')
        document.getElementById(popup).innerHTML = defaultPopup
    }
}


function edit(link) {
    document.getElementById('popup').classList.add('active')
    document.getElementById('popup').classList.remove('invisible')
    blur(true)
    document.getElementById("name").value = link["name"]
    document.getElementById("link").value = link["link"]
    document.getElementById("submit").innerHTML = `Update <img src="/static/images/right-angle.svg" alt="right arrow">`
    document.getElementById("submit").setAttribute('onClick', `registerBookmark(${link['id']})`)
    document.getElementById("title").innerText = "Edit your bookmark";
    window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
}


function delete_(link) {
    const deleteButton = document.getElementById("delete_button")
    window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
    document.getElementById("popup-delete").style.display = "flex"
    document.getElementById("popup-delete").classList.remove('invisible')
    document.getElementById("popup-delete").classList.add('active')
    document.getElementById("popup-delete").children[0].innerHTML = 'Are you sure you want to delete <b>'+link['name']+'</b>?'
    const newButton = deleteButton.cloneNode(true)
    deleteButton.parentNode.replaceChild(newButton, deleteButton)
    newButton.addEventListener('click', async () => {
        hide('popup-delete')
        await fetch('/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: link['id'], email: link['username'], type: 'bookmark'})
        })
        if ((global_bookmarks['bookmarks']).length === 0) {return location.reload()}
    })
    blur(true)
}


function share(link, link_el) {
    document.getElementById("popup-share").style.zIndex = "11"
    document.getElementById("popup-share").classList.remove('invisible')
    document.getElementById("popup-share").classList.add('active')
    document.getElementById("popup-share").style.display = {"none": "flex", "flex": "none"}[document.getElementById("popup-share").style.display]
    document.getElementById('popup-share-button').onclick = () => {shareLink(link)}
    blur(true)
    window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
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
            body: JSON.stringify({id: link['id'], email: link['username'], permanent: 'true', type: 'bookmark'})
        })
        location.reload()
    })
}


async function restore(id, email) {
    await fetch('/restore', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: id, email: email, type: 'bookmark'})
    })
    location.reload()
}


function createBookmark(link, id="insert") {
    let link_event = createElement('div', ['link'], link['id'])
    if (id === 'pending-links') {
        link_event.classList.add('pending-link')
    }
    const openBookmark = createElement('div', ['join-meeting'], '', '',
        {'events': {'onclick': () => {window.open(link['link'])}}})
    openBookmark.appendChild(createElement('p', ['name'], '', link['name']))
    openBookmark.appendChild(createElement('p', ['description'], '', 'Click to open bookmark'))
    link_event.appendChild(openBookmark)

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
        'Copy link': () => copyLink(link['link'], link['id'])}
        } else {
            buttons = {'Restore': () => restore(link['id'], link['username']), 'Delete': () => permDelete(link),
                'Copy link': () => copyLink(link['name'], link['id'])}
        }
        menu.style.height = '150px'
        for (const [key, value] of Object.entries(buttons)) {
            menu.appendChild(createElement('div', [], '', key, {'events': {'onclick': value}}))
            key !== 'Copy link' ? menu.appendChild(createElement('hr', ['menu_line'])) : null
        }
        link_event.appendChild(menu)
    }
    return link_event
}


function createPendingBookmarks(username, links) {
    const pendingLinks = createElement('div', ['pending-links'], 'pending-links')
    links.forEach((link) => {
        pendingLinks.appendChild(createBookmark(link, 'pending-links'))
    })

    pendingLinks.appendChild(createElement('hr', ['hr-pending-links'], 'hr-pending-links', ''))
    document.getElementById('insert').prepend(pendingLinks)
}


async function createBookmarks(username, links, id="insert") {
    await refresh(id)
    let newLinks = links.slice()
    newLinks.reverse()
    newLinks.forEach((link) => {
        document.getElementById(id).appendChild(createBookmark(link, id))
    })

    document.addEventListener('click', e => {
            Array.from(document.getElementsByClassName('menu')).forEach(i => {
                if (!['Copied!', 'Copy link'].includes(e.target.innerText) &&
                    !e.target.classList.contains('dot-menu') && !i.classList.contains('tutorial')) {
                    i.style.display = 'none'
                }
            })
        })

    if (global_bookmarks['pending-bookmarks'].length > 0) {
        createPendingBookmarks(username, global_bookmarks['pending-bookmarks'])
    }
}


async function loadBookmarks(username, id="insert") {
    if (!connected) {
        return
    }
    global_username = username
    webSocket = new WebSocket(`wss://linkjoin.xyz/database_ws?email=${encodeURIComponent(username)}&origin=bookmarks`)
    webSocket.onopen = () => {
        webSocket.send(JSON.stringify({'email': username}))
    }
    webSocket.onmessage = async (e) => {
        let bookmarks = JSON.parse(e.data)
        Object.entries(bookmarks).forEach(([categoryName, bookmarkCategory]) => {
            if (!['links', 'pending-links', 'deleted-links', 'update_id'].includes(categoryName)) {
                bookmarkCategory.forEach(bookmark => {
                    bookmark['superDisabled'] = org_disabled === 'true';
                })
            }
        })
        if (((global_bookmarks !== undefined && global_bookmarks['bookmarks'].length === 0) && bookmarks['bookmarks'].length === 1) ||
            (global_bookmarks !== undefined && global_bookmarks['bookmarks'].length === 1 && bookmarks['bookmarks'].length === 0)) {
            location.reload()
            return
        }
        global_bookmarks = bookmarks
        if (bookmarks['bookmarks'].length === 0 && !document.getElementById(id).classList.contains('empty') && pageLoaded) {
            location.reload()
        }
        await createBookmarks(username, bookmarks['bookmarks'], 'insert')
    }
    webSocket.onclose = () => {
        if (connected) {
            location.reload()
        }
        connected = false
    }
    webSocket.onerror = (e) => {
        console.log(e)
    }
    let bookmarks
    try {
        document.getElementById(id).style.display = 'flex'
    }
    catch {
        while (!connected) {
            await sleep(5000)
        }
        await refresh()
        await loadBookmarks(username)
    }

    while (global_bookmarks === undefined) {
        await sleep(500)
    }

    if (id === "insert") {
        bookmarks = global_bookmarks['bookmarks']
    }
    else {
        bookmarks = global_bookmarks['deleted-links']
    }
    id = id === 'deleted-bookmarks' ? 'deleted-bookmarks-body' : id
    const insert = document.getElementById(id)
    if (id !== 'insert') {
        blur(true)
    }
    if (bookmarks.toString() === '' && id === 'insert' && global_bookmarks['pending-bookmarks'].length === 0) {
        await refresh(id)
        document.getElementById("header-links").style.margin = "0 0 0 0"
        document.getElementById('links-search-container').classList.add('gone')
        document.getElementById("no-links-made").classList.remove("gone")
    }
    else if (bookmarks.toString() === '' && id !== 'insert') {
        insert.classList.add('empty')
        insert.innerHTML = `<h2>After you delete a bookmark, it will show up here.</h2>
                            <img src="/static/images/trash.svg" alt="trash can">`
        return
    }
    else {
        await createBookmarks(username, bookmarks, id)
    }

    defaultPopup = document.getElementById('popup').innerHTML
    if (error === 'link_not_found') {
        history.pushState('data', 'LinkJoin', '/links')
        await sendNotif('The bookmark you are trying to add could not be found. Please contact the owner of this bookmark for more information.', '#ba1a1a')
    }
    if (document.getElementsByClassName('highlight').length > 0) {
        document.getElementsByClassName('highlight')[0].scrollIntoView(true)
        await sleep(3000)
        document.getElementsByClassName('highlight')[0].style.background = 'none'
    }
    pageLoaded = true
}


async function registerBookmark(parameter) {
    disableButton(document.getElementById('submit'))
    if (parameter === 'tutorial') {location.reload()}
    const args = {
        name: document.getElementById("name").value,
        link: document.getElementById("link").value,
        id: parameter, email: global_username
    }
    const payload = {
        headers: {'Content-Type': 'application/json'},
        method: 'POST',
        body: JSON.stringify(args)
    }
    const url = parameter === 'register' ? '/create-bookmark' : '/edit-bookmark'
    if (!document.getElementById("name").value || !document.getElementById("link").value) {
        enableButton('submit')
    }
    if (!document.getElementById("name").value) {return document.getElementById("error").innerText = "Please provide a name for your meeting"}
    if (!document.getElementById("link").value) {return document.getElementById("error").innerText = "Please provide a link for your meeting"}
    if (account === 'false') {
        global_bookmarks.push(args)
        localStorage.setItem('links', JSON.stringify(global_bookmarks))
    }
    else {
        await fetch(url, payload)
    }
    hide('popup')
    if (global_bookmarks['bookmarks'].length === 1) {
        location.reload()
    }
}


function shareLink(link) {
    document.getElementById('popup-share-button').innerHTML = document.getElementById('popup-share-button').innerHTML.replace('Send', 'Sent!')
    let emails = []
    for (const i of document.getElementsByClassName('popup-share-email')) {
        if (i.style.color !== 'red') {
            emails.push(i.innerText)
        }
        else {
            console.log(`invalid email ${i.innerText}`)
        }
    }
    console.log(emails)
    let data = {
        email: global_username,
        emails: emails,
        link: link,
        type: 'bookmark'

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
        accept: accept,
        type: 'bookmark'
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


function searchBookmarks(value) {
    let visible = []
    for (const link of global_bookmarks['bookmarks']) {
        if (link['name'].toLowerCase().includes(value.toLowerCase()) || link['link'].toLowerCase().includes(value.toLowerCase())
         || (admin_view === 'true' && link['username'].toLowerCase().includes(value.toLowerCase()))) {
            visible.push(link)
        }
    }
    if (visible.length === 0) {
        document.getElementById('no-links-search').classList.remove('gone')
    }
    else if (!document.getElementById('no-links-search').classList.contains('gone')) {
        document.getElementById('no-links-search').classList.add('gone')
    }
    createBookmarks(global_username, visible)
}

// DUPLICATE FUNCTIONS FROM links.js - WILL MODULIZE SOON

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


async function logOut() {
    document.cookie = "email=; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
    await fetch(`/logout?email=${global_username}&session_id=${document.cookie.match('(^|;)\\s*session_id\\s*=\\s*([^;]+)')?.pop() || ''}`);
    document.cookie = "session_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
    location.replace('/login')
}


async function refresh(id="insert") {
    let insert = document.getElementById(id)
    if (insert) {
        while (insert.firstChild) {insert.removeChild(insert.firstChild)}
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


function verifyEmail(e) {
    if (e.keyCode === 13 && e.target.value !== '') {
        createShareEmail()
    }
}


function searchLinks(value) {
    let visible = []
    for (const link of global_bookmarks['bookmarks']) {
        console.log(link['time'])
        if (link['name'].toLowerCase().includes(value.toLowerCase()) || link['link'].toLowerCase().includes(value.toLowerCase())
         || (admin_view === 'true' && link['username'].toLowerCase().includes(value.toLowerCase()))) {
            visible.push(link)
        }
    }
    if (visible.length === 0) {
        document.getElementById('no-links-search').classList.remove('gone')
    }
    else if (!document.getElementById('no-links-search').classList.contains('gone')) {
        document.getElementById('no-links-search').classList.add('gone')
    }
    createBookmarks(global_username, visible)
}


function openMenu(el) {
    el.children[el.children.length-1].style.display = 'flex';
}


function copyLink(link, id) {
    if (link === 'tutorial') {
        return navigator.clipboard.writeText('https://linkjoin.xyz')
    }
    navigator.clipboard.writeText(link).then(async () => {
        document.getElementById(id).children[2].children[6].innerText = "Copied!"
        await sleep(2000)
        document.getElementById(id).children[2].children[6].innerText = "Copy link"
    })
}



