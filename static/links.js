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

function register_buttons(link_names) {
    buttons = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for (const button of buttons) {
        button_input = document.createElement('input')
        button_input.type = 'text'
        button_input.name = button
        button_input.style.opacity = 0
        if (document.getElementById(button).classList.contains("selected")) {
            button_input.value = "true"
        }
        else {
            button_input.value = "false"
        }
        document.getElementById("create").appendChild(button_input)
    }
}

async function load_links(username) {
    let start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
    let links = await start_json.json()
    if (links.toString() == '') {
        document.getElementById("header").style.margin = "0 0 0 0"
        const image = document.createElement("img");
        const image_attributes = {"src": "https://cdn.discordapp.com/attachments/716377034728931331/808917653422735420/Time_management-cuate.png", "height": "430px", "width": "450px", "style": "margin-top: -1vh; margin-left: 36vw;"}
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
        document.getElementById("header").style.margin = "0 0 80px 0"
        let iterator = 0;
        for (const link of links) {
            console.log(link)
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
            let activate_switch = document.createElement("button")
            activate_switch.classList.add("switch")

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
                console.log(link['id'])
                console.log(link)
                location.href = "/deactivate?id="+link["id"]})
            }
            link_event.appendChild(activate_switch)
            let edit = document.createElement("button")
            edit.classList.add("edit")
            console.log(link)
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

            })
            edit.innerText = "Edit"
            link_event.appendChild(edit)
            let delete_button = document.createElement("button")
            delete_button.classList.add("delete")
            delete_button.innerText = "Delete"
            delete_button.addEventListener("click", function() {
                document.getElementById("popup_delete").classList.remove("hidden")
                document.getElementById("delete_button").href = `/delete?id=${link['id']}`})
            link_event.appendChild(delete_button)
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