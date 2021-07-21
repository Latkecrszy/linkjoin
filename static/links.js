let global_username, global_sort, tutorial_complete
let tutorial_active = false;
let created = false;

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
}
function createElement(type="div", _class=[], id=null, text=null, style={}, html= null, other={}) {
    const newElement = document.createElement(type)
    _class.forEach((className) => newElement.classList.add(className))
    id !== null ? newElement.id = id : null
    newElement.innerText = text
    Object.entries(style).forEach(([key, value]) => newElement.style[key] = value)
    html !== null ? newElement.innerHTML = id : null
    Object.entries(other).forEach(([key, value]) => newElement[key] = value)
    return newElement
}



async function popUp(popup, link_names, premium="true") {
    if (premium === "false" && link_names.length >= 10) {
        document.documentElement.style.setProperty("--right", "-350px")
        document.getElementById("popup_premium").style.display = "flex"
        let position;
        for (position = -350; position <= 50; position += 3.5) {
            document.documentElement.style.setProperty("--right", `${position}px`)
            await sleep(1)
        }
        for (let amount = 1; amount <= 110; amount += 0.25) {
            document.documentElement.style.setProperty("--progress", `${amount}%`)
            await sleep(11)
        }
        while (position >= -350) {
            document.documentElement.style.setProperty("--right", `${position}px`)
            await sleep(1)
            position -= 3.5
        }
        return document.getElementById("popup_premium").style.display = "none"
    }
    hide('popup')
    document.getElementById(popup).style.display = "flex"
    const blur = document.getElementById("blur")
    const submit = document.getElementById("submit")
    blur.style.opacity = "0.4"
    blur.style.zIndex = "3"
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
    const date = new Date()
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
    document.getElementById("blur").style.zIndex = "-3"
    document.getElementById("blur").style.opacity = "0"
}

document.addEventListener("click", event => {if(event.target.matches("#days button")) event.target.classList.toggle("selected")})


async function load_links(username, sort) {
    console.log("restart")
    global_username = username
    global_sort = sort
    let link_events = []
    const insert = document.getElementById("insert")
    for (let i=0; i<3; i++) {
        insert.append(createElement("div", ["placeholder"]))
    }
    const start_json = await fetch(`/db?username=${username}`)
    const links = await start_json.json()
    if (links.toString() === '') {
        await refresh()
        document.getElementById("header_links").style.margin = "0 0 0 0"
        document.getElementById("disappear").classList.remove("gone")
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
            const link_dict = {"Mon": {}, "Tue": {}, "Wed": {}, "Thu": {}, "Fri": {}, "Sat": [], "Sun": {}, "dates": {}}
            const other_link_list = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": [], "Sat": [], "Sun": [], "dates": []}
            for (const link_info of links) {
                link_dict[link_info['days'][0]][parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`)] = link_info
                other_link_list[link_info['days'][0]].push(parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`))
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
        for (const link of final) {
            const link_event = createElement("div", ["link_event"], iterator.toString())
            const time = link["time"]
            const time_list = time.split(":")
            let pm = "am"
            if (parseInt(time_list[0]) === 12) {pm = "pm"}
            else if (parseInt(time_list[0]) === 24) {time_list[0] = 12}
            else if (parseInt(time_list[0]) > 12) {time_list[0] = parseInt(time_list[0]) - 12; pm = "pm"}
            link_event.appendChild(createElement("div", ["time"], null, (time_list.join(":"))+" "+pm))
            const nameContainer = createElement("div", [], null, null, {'cursor': 'pointer'})
            const name = createElement("div", ["link_event_title"], null, link['name'])
            if (link["active"] === "true") {name.style.color = "#2B8FD8"}
            else {name.style.color = "#B7C0C7"}
            const join_now = createElement("div", ['join_now'], null, "Click to join the room now")
            nameContainer.addEventListener("click", () => {window.open(link['link']); console.log("clicked")})
            nameContainer.append(name, join_now)
            const days = createElement("div", ["days"], null, link['days'].join(", "))
            link_event.append(nameContainer, days)
            const buttons = createElement("img", ["menu_buttons"], null, null, {}, null,
                {src: "static/images/ellipsis.svg", height: 20, width: 8})
            buttons.addEventListener("click", (e) => {menu.style.display = "flex"; e.stopPropagation()})
            /*Create the menu*/
            const menu = createElement("div", ["menu"])
            menu.addEventListener("click", (e) => e.stopPropagation())
            /*Make the edit button*/
            const edit = createElement("div", [], null, "Edit")
            edit.addEventListener("click", () => {
                const element = document.getElementById("popup")
                element.style.display = "flex"
                document.getElementById("blur").style.opacity = "0.4"
                document.getElementById("blur").style.zIndex = "3"
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
                document.getElementById("submit").addEventListener("click", () => register_link(link['id']))
                document.getElementById("title").innerText = "Edit your meeting"
                for (let day of ["Sun", "Mon","Tue", "Wed", "Thu", "Fri", "Sat"]) {document.getElementById(day).classList.remove("selected")}
                for (let day_abbrev of link['days']) {
                    if (document.getElementById(day_abbrev)) {
                        document.getElementById(day_abbrev).classList.add("selected")
                    }
                }
                document.getElementById(link['repeat']).selected = "selected"
                if (link['starts']) {document.getElementById(link['starts']).selected = "selected"}
                window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
            })
            /*Make the first line*/
            const hr = createElement("hr", ["menu_line"])
            /*Make the delete button*/
            const del = createElement("div", [], null, "Delete")
            del.addEventListener("click", () => {
                window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
                document.getElementById("popup_delete").style.display = "flex"
                document.getElementById("delete_button").addEventListener('click', async () => {
                    hide('popup_delete')
                    await fetch(`/delete?id=${link['id']}`)
                    await refresh()
                    await load_links(username, sort)})
                })
            /*Make the second line*/
            const hr2 = createElement("hr", ["menu_line"])
            /*Make the share button*/
            const share = createElement("div", [], null, "Share")
            share.addEventListener("click", () => {
                document.getElementById("popup_share").style.zIndex = "11"
                document.getElementById("popup_share").style.display = {"none": "flex", "flex": "none"}[document.getElementById("popup_share").style.display]
                document.getElementById("share_link").value = link['share']
                document.getElementById("blur").style.opacity = "0.4";
                document.getElementById("blur").style.zIndex = "3"
                window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
                })

            /*Add menu click event*/
            document.addEventListener("click", () => menu.style.display = "none")
            /*Append everything*/
            menu.append(edit, hr, del, hr2, share)
            /*Make the password button and third line*/
            if ("password" in link) {
                menu.style.height = "145px"
                const hr3 = createElement("hr", ["menu_line"])
                const password = createElement("div", [], link['id'].toString(), "Password")
                password.addEventListener('click', async () => {
                    navigator.clipboard.writeText(link['password']).then(async () => {
                        password.innerText = "Copied!"
                        p.remove()
                        await sleep(2000)
                        password.innerText = "Password"
                    })
                })
                menu.append(hr3, password)
            }
            link_event.appendChild(menu)

            /*Create the switch*/
            const toggleSwitchCheckbox = createElement("input", ["checkbox"], `toggle${iterator}`, null,
                {}, null, {type: "checkbox", checked: true})
            link_event.appendChild(toggleSwitchCheckbox)
            const toggleSwitch = createElement("label", ["switch"], null, null, {}, null,
                {htmlFor: `toggle${iterator}`})
            toggleSwitch.addEventListener("click", async () => {
                await fetch(`/disable?id=${link['id']}`)
                await refresh()
                await load_links(username, sort)
            })
            link_event.append(toggleSwitch, buttons)
            if (link['active'] === "false") {
                link_event.style.opacity = "0.6"
                name.style.color = "#B7C0C7"
                nameContainer.style.opacity = "0.7"
                toggleSwitchCheckbox.checked = false
            }
            link_events.push(link_event)
            iterator += 1
        }
    }
    document.getElementById("click_to_copy").addEventListener('click', async () => {
        navigator.clipboard.writeText(document.getElementById("share_link").value).then(async () => {
            document.getElementById("click_to_copy").innerText = "Copied!"
            await sleep(2000)
            document.getElementById("click_to_copy").innerText = "Click to Copy"
        })
    })
    let tutorial_completed = await fetch(`https://linkjoin.xyz/tutorial_complete?username=${username}`)
    tutorial_completed = await tutorial_completed.json()
    if (tutorial_completed['tutorial'] !== "done") {await tutorial(tutorial_completed['tutorial'])}
    await check_day(username)
    //await sleep(200)
    await refresh()
    link_events.forEach((link) => {insert.appendChild(link)})
    await check_if_tutorial()
    clearInterval(open)
    start(username, links, sort)
    // MAKE IT STOP RUNNING THE NEWTAB MULTIPLE TIMES
}

//window.addEventListener("resize", () => {document.getElementById("blur").style.height = `${document.getElementById("insert").offsetHeight+500}px`})
async function check_day(username) {
    let date = new Date()
    let start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
    let links = await start_json.json()
    let day = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[parseInt(date.getDay())]
    let children = document.getElementById("days").children
    if (links.length <= 3) {
        for (let child of children) {
            if (child.value === day) {child.classList.add("selected")}
        }
    }
}

function sort() {location.replace("/sort?sort="+document.getElementById("sort").value.toString())}


async function register_link(parameter) {
    if (created) {return}
    created = true
    let name = document.getElementById("name").value
    let link = document.getElementById("link").value
    let hour = parseInt(document.getElementById("hour").value)
    let text = document.getElementById("text_select").value
    let minute = document.getElementById("minute").value
    let repeats = document.getElementById("select").value
    if (document.getElementById("am").value === "pm") {if (hour !== 12) {hour += 12}}
    else {if (hour === 12) {hour += 12}}
    let time = `${hour}:${minute}`
    let password = document.getElementById("password").value
    let days = []
    for (let child of document.getElementById("days").children) {
        if (child.classList.contains("selected")) {
            days.push(child.value)
        }
    }
    let starts = parseInt(document.getElementById("starts_select").value)*days.length
    let url
    if (parameter === "register") {
        url = `/register?name=${name}&link=${link}&time=${time}&repeats=${repeats}&days=${days}&starts=${starts}&text=${text}`
    }
    else {
        url = `/update?name=${name}&link=${link}&time=${time}&repeats=${repeats}&days=${days}&id=${parameter}&starts=${starts}&text=${text}`
    }
    if (password.length > 0) {url += `&password=${password}`}
    if (!name) {return document.getElementById("error").innerText = "Please specify a name for your meeting"}
    if (!link) {return document.getElementById("error").innerText = "Please specify a link for your meeting"}
    if (days.length === 0) {return document.getElementById("error").innerText = "Please specify days or dates for your meeting."}
    skipTutorial()
    url = url.replace("#", "%23")
    hide('popup')
    await fetch(url)
    location.reload()
}

function logOut() {document.cookie = "email=; expires=Thu, 01 Jan 1970 00:00:00 UTC;"; location.replace('/login')}


function checkNever() {
    if (document.getElementById("select").value === "never") {document.getElementById("repeats_text").innerText = "Repeats"}
    else {document.getElementById("repeats_text").innerText = "Repeats every"}
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


async function tutorial(item, skip) {
    tutorial_active = true
    item = parseInt(item)
    if (document.getElementById("blur").style.opacity !== "0.4") {
        document.getElementById("blur").style.opacity = "0.4";
        document.getElementById("blur").style.zIndex = "3"
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
            await fetch(`https://linkjoin.xyz/tutorial?username=${global_username}&step=1`)
            document.getElementById("box").style.zIndex = "5"
            document.getElementById("box").style.background = "rgba(255, 255, 255, 0.1)"
            document.getElementById("check_popup").style.display = "none"
            return newWindow.close()
        }
        await fetch(`https://linkjoin.xyz/tutorial?username=${global_username}&step=0`)
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
        await fetch(`https://linkjoin.xyz/tutorial?username=${global_username}&step=done`)
        tutorial_complete = true
    }
    await fetch(`https://linkjoin.xyz/tutorial?username=${global_username}&step=${item}`)
    document.getElementById("add_number_div").style.display = "none"
    try {document.getElementById(`tutorial${item}`).style.display = "flex"}
    catch {}
    try {document.getElementById(`tutorial${parseInt(item)-1}`).style.display = "none"}
    catch {}
}

async function skipTutorial() {return await fetch(`https://linkjoin.xyz/tutorial?username=${global_username}&step=done`)}


async function refresh() {
    let insert = document.getElementById("insert")
    while (insert.firstChild) {insert.removeChild(insert.firstChild)}
}

document.addEventListener("click", x => {if (x.target.matches("#hamburger") || x.target.matches("#line1") || x.target.matches("#line2") || x.target.matches("#line3")) {document.getElementById("hamburger").classList.toggle("expand"); document.getElementById("hamburger_dropdown").classList.toggle("expand")}})


async function add_number() {
    let country = await fetch('https://linkjoin.xyz/location')
    country = await country.json()
    const countryCode = countryCodes[country['country']]
    console.log(countryCodes)
    console.log(country['country'])
    console.log(countryCodes[country['country']])
    let number = document.getElementById("number").value
    await fetch(`/add_number?username=${global_username}&countrycode=${countryCode['code']}&number=${number}`)
    document.getElementById("add_number_div").style.display = "none"
    document.getElementById("blur").style.zIndex = "-3"
    document.getElementById("blur").style.opacity = "0"
}

function show_add_number() {
    document.getElementById("add_number_div").style.display = "block"
        let blur = document.getElementById("blur")
        blur.style.opacity = "0.4"
        blur.style.zIndex = "3"
}

async function no_add_number() {
    if (number === "None") {number = ''}
    await fetch(`/add_number?username=${global_username}&countrycode=&number=${number}`)
    document.getElementById("add_number_div").style.display = "none"
    document.getElementById("blur").style.zIndex = "-3"
    document.getElementById("blur").style.opacity = "0"
}


async function check_if_tutorial() {
    let tutorial_completed = await fetch(`https://linkjoin.xyz/tutorial_complete?username=${global_username}`)
    tutorial_completed = await tutorial_completed.json()
    console.log(tutorial_completed['tutorial'])
    console.log(number)
    if (tutorial_completed['tutorial'] === "done") {
        if (number === "None") {
        show_add_number()
    }
    }
}

document.addEventListener("click", (e) => {
    if (e.target.id !== "hamburger_dropdown" && e.target.id !== "hamburger" &&
        !document.getElementById("hamburger").contains(e.target)) {
    document.getElementById("hamburger_dropdown").classList.remove("expand")
    document.getElementById("hamburger").classList.remove("expand")
}})
