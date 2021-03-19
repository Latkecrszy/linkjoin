let noSleep = new NoSleep()
noSleep.disable()

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function popUp(popup) {
    popup = document.getElementById(popup)
    popup.style.display = "flex"
    document.getElementById("page").classList.toggle("blurred")
    document.getElementsByTagName("html")[0].style.background = "#040E1A"
    document.getElementById("name").value = null
    document.getElementById("link").value = null
    document.getElementById("hour").value = null
    document.getElementById("minute").value = null
    document.getElementById("password").value = null
    document.getElementById("submit").innerHTML = null
    document.getElementById("submit").innerText = "Create"
    document.getElementById("submit_dates").innerHTML = null
    document.getElementById("submit_dates").innerText = "Create"
    document.getElementById("submit_dates").setAttribute("onclick", `register_link("register")`)
    document.getElementById("submit").setAttribute("onclick", `register_link("register")`)
    document.getElementById("title").innerText = "Schedule a new meeting"
    document.getElementById('week').selected = "selected"

    let children = document.getElementById("days").children
    for (let i=0; i < children.length; i++) {
        let date = new Date()
        if (children[i].value != {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[parseInt(date.getDay())]) {
            children[i].classList.remove("selected")
        }
    }
    document.getElementById("0").selected = "selected"
    check()
}

function hide(popup) {
    popup = document.getElementById(popup)
    popup.style.display = "none"
    document.getElementById("page").classList.toggle("blurred")
    document.getElementsByTagName("html")[0].style.background = "#091B30"
    check()
}

function check() {
    checkbox = document.getElementById("repeats")
    if (checkbox.checked) {
        if (document.getElementById("repeats_text").innerText.includes("every") == false) {
            document.getElementById("repeats_text").innerText += " every"
            document.getElementById("days").classList.remove("hidden")
            document.getElementById("starts").classList.remove("hidden")
            document.getElementById("select").classList.remove("hidden")
            document.getElementById("dates_container").style.display = "none"
            document.getElementById("first_date").classList.add("gone")
            document.getElementById("add_field").classList.add("gone")
            document.getElementById("submit").classList.remove("gone")

        }
    }
    else {
        document.getElementById("repeats_text").innerText = "Repeats"
        document.getElementById("days").classList.add("hidden")
        document.getElementById("starts").classList.add("hidden")
        document.getElementById("select").classList.add("hidden")
        document.getElementById("dates_container").style.display = "flex"
        document.getElementById("first_date").classList.remove("gone")
        document.getElementById("add_field").classList.remove("gone")
        document.getElementById("submit").classList.add("gone")
    }
}

document.addEventListener("click", event => {
  if(event.target.matches("#days button")) event.target.classList.toggle("selected");
})


async function load_links(username, sort) {
    let start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
    let links = await start_json.json()
    if (links.toString() == '') {
        document.getElementById("header_links").style.margin = "0 0 0 0"
        document.getElementById("disappear").classList.remove("gone")
    }
    else {
        let final = []
        if (sort == "day") {
            let link_list = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": [], "Sat": [], "Sun": [], "dates": []}
            for (const link_info of links) {
                if (["week", "2 weeks", "3 weeks", "4 weeks"].includes(link_info['repeat'])) {
                    link_list[JSON.parse(link_info["days"].replaceAll("'", '"'))[0]].push(link_info)
                }
                else {
                    link_list['dates'].push(link_info)
                }

            }
            for (const day in link_list) {
                for (let key of link_list[day]) {
                    final.push(key)
                }
            }
        }
        else if (sort == "time") {
            let day_nums = {"Sun": 0.001, "Mon": 0.002, "Tue": 0.003, "Wed": 0.004, "Thu": 0.005, "Fri": 0.006, "Sat": 0.007}
            let times = []
            let link_time_list = {}
            for (const link_info of links) {
                if ('days' in link_info) {
                    times.push((parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`)+day_nums[JSON.parse(link_info["days"].replaceAll("'", '"'))[0]]))
                    link_time_list[(parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`)+day_nums[JSON.parse(link_info["days"].replaceAll("'", '"'))[0]])] = link_info
                }
                else {
                    times.push(parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`))
                    link_time_list[parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`)] = link_info
                }
            }
            for (const link_time of times.sort((a, b) => a - b)) {
                final.push(link_time_list[link_time])
            }
        }
        else if (sort == "datetime") {
            let link_list = {"Mon": {}, "Tue": {}, "Wed": {}, "Thu": {}, "Fri": {}, "Sat": [], "Sun": {}, "dates": {}}
            let other_link_list = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": [], "Sat": [], "Sun": [], "dates": []}
            let final_link_list = {"Mon": {}, "Tue": {}, "Wed": {}, "Thu": {}, "Fri": {}, "Sat": [], "Sun": {}, "dates": {}}
            console.log(links)
            for (const link_info of links) {
                if (["week", "2 weeks", "3 weeks", "4 weeks"].includes(link_info['repeat'])) {
                    link_list[JSON.parse(link_info["days"].replaceAll("'", '"'))[0]][parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`)] = link_info
                    other_link_list[JSON.parse(link_info["days"].replaceAll("'", '"'))[0]].push(parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`))
                }
                else {
                    link_list['dates'][parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`)] = link_info
                    other_link_list['dates'].push([parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`)])

                }

            }
            for (let day_name in other_link_list) {
                other_link_list[day_name] = other_link_list[day_name].sort((a, b) => a - b)
            }
            console.log(other_link_list)
            for (let day_name in other_link_list) {
                for (let time_info of other_link_list[day_name]) {
                    final.push(link_list[day_name][time_info])
                }
            }
        }
        else {
            final = links
        }
        document.getElementById("header_links").style.margin = "0 0 200px 0"
        let iterator = 0;
        console.log(final)
        for (let link of final) {
            link_event = document.createElement("div")
            link_event.classList.add("link_event")
            link_event.id = iterator.toString()

            let time_div = document.createElement("div")
            time_div.classList.add("time")
            let time = link["time"]
            let time_list = time.split(":")
            let pm = "am"
            if (parseInt(time_list[0]) == 12) {
                pm = "pm"
            }
            else if (parseInt(time_list[0]) == 24) {
                pm = "am"
                time_list[0] = 12
            }
            else if (parseInt(time_list[0]) > 12) {
                time_list[0] = parseInt(time_list[0]) - 12
                pm = "pm"
            }
            time = time_list.join(":")
            time += " "+pm
            time_div.innerText = time
            link_event.appendChild(time_div)
            let name = document.createElement("div")
            let name_container = document.createElement("div")
            name_container.style.cursor = "pointer"
            name.classList.add("link_event_title")
            name.innerText = link["name"]
            if (link["active"] == "true") {
                name.style.color = "#2B8FD8"
            }
            else {
                name.style.color = "#B7C0C7"
            }
            let join_now = document.createElement("div")
            join_now.classList.add("join_now")
            join_now.innerText = "Click to join the room now"
            name.setAttribute("onclick", `window.open("${link['link']}")`)
            join_now.setAttribute("onclick", `window.open("${link['link']}")`)
            name_container.appendChild(name)

            name_container.appendChild(join_now)

            link_event.appendChild(name_container)
            let days = document.createElement("div")
            days.classList.add("days")
            let days_list;
            if (["week", "2 weeks", "3 weeks", "4 weeks"].includes(link['repeat'])) {
                days_list = link["days"].replaceAll("'", '"')
                days_list = JSON.parse(days_list)
                days.innerText = days_list.join(", ")
            }
            else {
                let dates_list = []
                let months = {"01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun", "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"}
                for (let date_info of JSON.parse(link['dates'].replaceAll("'", '"'))) {
                    dates_list.push(`${months[date_info["month"].toString()]} ${parseInt(date_info["day"])}, ${date_info["year"]}`)
                }
                days.innerText = dates_list.join("; ")
            }
            link_event.appendChild(days)
            let buttons = document.createElement("div")
            buttons.classList.add("buttons_container")
            if ('password' in link) {
                let copy = document.createElement("button")
                copy.innerText = "Password"
                copy.id = link['id'].toString()
                copy.classList.add("function_button")
                copy.style.background = "#37123C"
                copy.addEventListener('click', async function copyText() {
                    let p = document.createElement("input")
                    p.value = link['password']
                    document.getElementById("links_body").appendChild(p)
                    p.select()
                    document.execCommand("copy")
                    copy.innerText = "Copied!"
                    p.remove()
                    await sleep(2000)
                    copy.innerText = "Password"
                })
                buttons.appendChild(copy)
            }

            let share = document.createElement("button")
            share.classList.add("function_button")
            share.style.background = "#E0FF4F"
            share.innerText = "Share"
            share.style.color = "black"
            share.addEventListener("click", function openShare() {
                let state = {"none": "flex", "flex": "none"}[document.getElementById("popup_share").style.display]
                document.getElementById("popup_share").style.display = state
                document.getElementById("share_link").value = link['share']
                document.getElementById("page").classList.toggle("blurred")
                document.getElementsByTagName("html")[0].style.background = "#040E1A"
                window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
                })

            document.getElementById("click_to_copy").addEventListener('click', async function copyText() {
                document.getElementById("share_link").select()
                document.execCommand("copy")
                document.getElementById("click_to_copy").innerText = "Copied!"
                await sleep(2000)
                document.getElementById("click_to_copy").innerText = "Click to Copy"
            })
            buttons.appendChild(share)
            let activate_switch = document.createElement("button")
            activate_switch.classList.add("function_button")
            if (link['active'] == "false") {
                link_event.style.opacity = 0.5
                activate_switch.style.background = "#B7C0C7"
                activate_switch.style.color = "black"
                activate_switch.innerText = "Activate"
                activate_switch.addEventListener("click", function() {
                location.href = "/activate?id="+link["id"]})
            }
            else {
                link_event.style.opacity = 1
                activate_switch.style.background = "#2B8FD8"
                activate_switch.style.color = "white"
                activate_switch.innerText = "Deactivate"
                activate_switch.addEventListener("click", function() {
                location.href = "/deactivate?id="+link["id"]})
            }
            buttons.appendChild(activate_switch)
            let edit = document.createElement("button")
            edit.classList.add("function_button")
            edit.style.background = "#27FB6B"
            edit.addEventListener("click", function() {
                link_event = document.getElementById(iterator.toString())
                element = document.getElementById("popup")
                element.style.display = "flex"
                document.getElementById("page").classList.add("blurred")
                document.getElementsByTagName("html")[0].style.background = "#040E1A"
                check()
                document.getElementById("name").value = link["name"]
                document.getElementById("link").value = link["link"]
                if ("password" in link) {document.getElementById("password").value = link["password"]}
                else {document.getElementById("password").value = null}
                if (parseInt(link['time'].split(":")[0]) == 12) {
                    document.getElementById("pm").selected = "selected"
                    document.getElementById("hour").value = 12
                }
                else if (parseInt(link['time'].split(":")[0]) == 24) {
                    document.getElementById("hour").value = 12
                }
                else if (parseInt(link['time'].split(":")[0]) > 12) {
                    document.getElementById("hour").value = parseInt(link['time'].split(":")[0])-12
                    document.getElementById("pm").selected = "selected"
                }
                else {
                    document.getElementById("hour").value = link['time'].split(":")[0]
                }
                document.getElementById("minute").value = link['time'].split(":")[1]
                document.getElementById("submit").innerText = "Update"
                document.getElementById("submit").setAttribute("onclick", `register_link("${link['id']}")`)
                document.getElementById("submit_dates").innerText = "Update"
                document.getElementById("submit_dates").setAttribute("onclick", `register_link("${link['id']}")`)
                document.getElementById("title").innerText = "Edit your meeting"
                for (let day_abbrev of days_list) {
                    if (document.getElementById(day_abbrev)) {
                        let currentDay = new Date()
                        currentDay = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[parseInt(currentDay.getDay())]
                        document.getElementById(currentDay).classList.remove("selected")
                        if (!document.getElementById(day_abbrev).classList.contains("selected")) {
                            document.getElementById(day_abbrev).classList.add("selected")
                        }

                    }
                }
                document.getElementById(link['repeat']).selected = "selected"
                document.getElementById(link['starts']).selected = "selected"
                window.scrollTo({top: 0, left: 0, behavior: 'smooth'})

            })
            edit.innerText = "Edit"
            edit.style.color = "black"
            buttons.appendChild(edit)
            let delete_button = document.createElement("button")
            delete_button.classList.add("function_button")
            delete_button.style.background = "#A40606"
            delete_button.innerText = "Delete"
            delete_button.addEventListener("click", function() {
                window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
                document.getElementById("popup_delete").style.display = "flex"
                document.getElementById("delete_button").href = `/delete?id=${link['id']}`})
            buttons.appendChild(delete_button)
            link_event.appendChild(buttons)
            if (link['active'] == "false") {
                link_event.opacity = 0.6
            }
            document.getElementById("insert").appendChild(link_event)
            iterator += 1
        }
    }
    check_day(username)
    await NewTab(username, links)
}

async function check_day(username) {
    let date = new Date()
    let start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
    let links = await start_json.json()
    let day = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[parseInt(date.getDay())]
    let children = document.getElementById("days").children
    if (links.length <= 3) {
        for (let i = 0; i < children.length; i++) {
            let child = children[i];
            if (child.value == day) {
                child.classList.add("selected")
            }
        }
    }
}


function redirect(redirect_to) {
    window.open(redirect_to)
}

function sort() {
    location.href = "/sort?sort="+document.getElementById("sort").value.toString()
}


function register_link(parameter) {
    let form_element = document.getElementById("create")
    let name = document.getElementById("name").value
    let link = document.getElementById("link").value
    let hour = parseInt(document.getElementById("hour").value)
    let minute = parseInt(document.getElementById("minute").value)
    if (document.getElementById("am").value == "pm") {
        if (hour != 12) {hour += 12}
    }
    else {
        if (hour == 12) {hour += 12}
    }
    let time = `${hour}:${minute}`
    let password = document.getElementById("password").value
    let url;
    if (!document.getElementById("repeats").checked) {
        let dates = [document.getElementById("first_date").value.replaceAll(" ", "-")]
        for (let x = 0; x < document.getElementById("dates").children.length; x++) {
            let element = document.getElementById("dates").children[x];
            dates.push((element.value).replaceAll(" ", "-"))
        }
        if (parameter == "register") {
            url = `/register?name=${name}&link=${link}&time=${time}&repeats=none&dates=${dates}`
        }
        else {
            url = `/update?name=${name}&link=${link}&time=${time}&repeats=none&dates=${dates}&id=${parameter}`
        }

    }
    else {
        let days = []
        for (let x = 0; x < document.getElementById("days").children.length; x++) {
            if (document.getElementById("days").children[x].classList.contains("selected")) {
                days.push(document.getElementById("days").children[x].value)
            }
        }
        if (parameter == "register") {
            url = `/register?name=${name}&link=${link}&time=${time}&repeats=${document.getElementById("select").value}&days=${days}&starts=${parseInt(document.getElementById("starts_select").value)*days.length}`
        }
        else {
            url = `/update?name=${name}&link=${link}&time=${time}&repeats=${document.getElementById("select").value}&days=${days}&id=${parameter}&starts=${parseInt(document.getElementById("starts_select").value)*days.length}`
        }
    }
    if (password.length > 0) {url += `&password=${password}`}
    location.href = url
}

function logOut() {
    document.cookie = "login_info=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    location.reload()
}