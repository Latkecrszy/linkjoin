async function showNotes(changing) {
    window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
    const notes = await fetch('/notes', {headers: {'email': global_username}}).then(r => r.json())
    if (notes.length !== 0) {
        if (changing !== true) {
            notesInfo['index'] = 0
        }
        if (notesInfo['notes'] === undefined || notesInfo['notes'].length === notesInfo['index']) {
            notesInfo['notes'] = notes
        }
        await popUp('popup-notes')
        notesInfo['id'] = notesInfo['notes'][parseInt(notesInfo['index'])]['id']
        notesInfo['name'] = notesInfo['notes'][notesInfo['index']]['name']
        if (notesInfo['index'] === 0) {
            disableButton(document.getElementsByClassName('notes_button back')[0], false)
        }
        else {
            enableButton('notes_button back')
        }

        if (notesInfo['index'] === notesInfo['notes'].length-1) {
            disableButton(document.getElementsByClassName('notes_button next')[0], false)
        }
        else {
            enableButton('notes_button next')
        }

        document.getElementById('popup-notes').children[2].innerText = `Meeting notes for ${notesInfo['notes'][notesInfo['index']]['name']}`
        const html = await fetch('/markdown_to_html',
        {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({markdown: notesInfo['notes'][notesInfo['index']]['markdown']})}).then(r => r.text())
        document.getElementById('notes_div').innerHTML = html
    }
    else {
        await sendNotif('You do not have any meeting notes. Try creating some from the dot menus of your links!', '#ba1a1a')
    }
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
    notesInfo['notes'][notesInfo['index']]['markdown'] = document.getElementById('notes_textarea').value

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