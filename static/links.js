function popUp() {

    element = document.getElementById("popup")
    element.classList.remove("hidden")
    document.getElementById("main_page").classList.add("blurred")
    html.style.background = "#040E1A"
    document.getElementById("name").value = null
    document.getElementById("link").value = null
    document.getElementById("submit").innerHTML = null
    document.getElementById("submit").innerText = "Create"
    document.getElementById("create").action = "/added"
    document.getElementById("popup_schedule").innerText = "Schedule a new meeting"
    html.style.overflow = "hidden"
    check()
}

function hide() {
    element = document.getElementById("popup")
    element.classList.add("hidden")
    document.getElementById("main_page").classList.remove("blurred")
    html.style.background = "#091B30"
    html.style.overflow = "auto"
    document.getElementById("header").style.background = "#142539"

}

function check() {
    checkbox = document.getElementById("repeats")
    if (checkbox.checked) {
        if (document.getElementById("repeats_text").innerText.includes("every") == false) {
            document.getElementById("repeats_text").innerText += " every"
        }
    }
    else {
        document.getElementById("repeats_text").innerText = "Repeats"
        document.getElementById("days").classList.add("hidden")
    }
}

function change_color(day) {
    day_button = document.getElementById(day)
    if (day_button.classList.contains("selected")) {
        day_button.classList.remove("selected")
        day_button.classList.add("deselected")
    }
    else {
         day_button.classList.add("selected")
         day_button.classList.remove("deselected")
    }
}


async function load_links(username, sort) {
    let start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
    let links = await start_json.json()
    if (links.toString() == '') {
        document.getElementById("header").style.margin = "0 0 0 0"
        const image = document.createElement("img");
        const image_attributes = {"src": "{{ url_for('static', filename='images/links_loader.png') }}", "height": "430px", "width": "450px", "style": "margin-top: -1vh; margin-left: 36vw;"}
        for (const attribute in image_attributes) {
            image.setAttribute(attribute, image_attributes[attribute])
        }
        const click_plus = document.createElement("div")
        click_plus.classList.add("click_the_plus")
        click_plus.innerText = "Click the + button to start scheduling your meetings!"
        insert = document.getElementById("insert_things")
        insert.appendChild(image)
        insert.appendChild(click_plus)
    }
    else {
        console.log(sort)
        let final = []
        if (sort == "day") {
            console.log("day sorting")
            let link_list = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": [], "Sat": [], "Sun": []}
            for (const link_info of links) {
                console.log(JSON.parse(link_info["days"].replaceAll("'", '"')))
                link_list[JSON.parse(link_info["days"].replaceAll("'", '"'))[0]].push(link_info)
            }
            console.log(link_list)
            for (const day in link_list) {
                for (const key of link_list[day]) {
                    console.log(day)
                    console.log(key)
                    console.log(link_list[day])
                    final.push(link_list[day])
                }
            }
        }
        else if (sort == "time") {
            let times = []
            console.log("time sorting")
            let link_time_list = {}
            for (const link_info of links) {
                times.push(parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`))
                link_time_list[parseFloat(`${link_info['time'].split(":")[0]}.${link_info['time'].split(":")[1]}`)] = link_info
            }
            times = times.sort((a, b) => a - b)
            for (const link_time of times) {
                final.push(link_time_list[link_time])
            }
        }
        else {
            final = links
            console.log("not sorting")
        }
        console.log(final)
        document.getElementById("header").style.margin = "0 0 80px 0"
        let iterator = 0;
        for (const link of final) {
            link_event = document.createElement("div")
            link_event.classList.add("link_event")
            link_event.id = iterator.toString()
            if (iterator == 0) {
                link_event.style.margin = "80px 0 0 10vw"
            }
            let time_div = document.createElement("div")
            time_div.classList.add("time")
            let time = link["time"]
            let time_list = time.split(":")
            let pm = "am"
            if (parseInt(time_list[0]) == 12) {
                pm = "pm"
            }
            else if (parseInt(time_list[0]) > 11) {
                time_list[0] = parseInt(time_list[0]) - 12
                pm = "pm"
            }
            time = time_list.join(":")
            time += " "+pm
            time_div.innerText = time
            link_event.appendChild(time_div)
            let name = document.createElement("div")
            let name_container = document.createElement("div")
            name_container.classList.add("name_container")
            name.classList.add("link_event_title")
            name.innerText = link["name"]
            if (link["active"] == "true") {
                name.style.color = "#2B8FD8"
            }
            else {
                name.style.color = "#B7C0C7"
            }
            name_container.appendChild(name)
            let join_now = document.createElement("div")
            join_now.classList.add("join_now")
            join_now.innerText = "Click to join the room now"
            name_container.appendChild(join_now)
            redirect_to = `redirect("${link["link"]}")`
            name_container.setAttribute("onclick", redirect_to)
            link_event.appendChild(name_container)
            let days = document.createElement("div")
            days.classList.add("days")
            let days_list = link["days"].replaceAll("'", '"')
            days_list = JSON.parse(days_list)
            days.innerText = days_list.join(", ")
            link_event.appendChild(days)
            let buttons = document.createElement("div")
            buttons.classList.add("buttons_container")
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
                element.classList.remove("hidden")
                document.getElementById("main_page").classList.add("blurred")
                html.style.background = "#040E1A"
                check()
                document.getElementById("name").value = link["name"]
                document.getElementById("link").value = link["link"]
                document.getElementById("submit").innerText = "Update"
                document.getElementById("create").action = "/update?id="+link["id"]
                document.getElementById("popup_schedule").innerText = "Edit your meeting"
                window.scrollTo({top: 0, left: 0, behavior: 'smooth'})

            })
            edit.innerText = "Edit"
            buttons.appendChild(edit)
            let delete_button = document.createElement("button")
            delete_button.classList.add("function_button")
            delete_button.style.background = "#A40606"
            delete_button.style.color = "white"
            delete_button.innerText = "Delete"
            delete_button.addEventListener("click", function() {
                window.scrollTo({top: 0, left: 0, behavior: 'smooth'})
                document.getElementById("popup_delete").classList.remove("hidden")
                document.getElementById("delete_button").href = `/delete?id=${link['id']}`})
            buttons.appendChild(delete_button)
            link_event.appendChild(buttons)
            if (link['active'] == "false") {
                link_event.opacity = 0.6
            }

            document.getElementById("insert_things").appendChild(link_event)
            iterator += 1
        }
    }
}
function redirect(redirect_to) {
    window.open(redirect_to)
}