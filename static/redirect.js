let open, user_links

function minutes(time, before) {
    let minute = parseInt(time.split(":")[1])-before
    let hour = parseInt(time.split(":")[0])
    if (minute < 0) {
        minute = 60+minute
        hour -= 1
        if (hour === 0) {
            hour = 24
        }
    }
    return `${hour}:${minute}`
}

async function start(username, links, sort) {
    open = setInterval(async () => {
        const newDate = new Date((Date.now() + 60000*open_early))
        const day = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[newDate.getDay()]
        let minute = newDate.getMinutes()
        if (minute.toString().length === 1) {minute = `0${minute}`}
        const time = `${newDate.getHours()}:${minute}`
        user_links = await db(username)
        for (let link of user_links) {
            let days = link['days']
            if (link['active'] === "false" || link['time'] !== time || !(days.includes(day))) {
                continue
            }
            if (parseInt(link['starts']) > 0) {
                continue
            }
            window.open(link['link'])
            if (link['repeat'] === 'never') {
                if (link['days'].length > 1) {
                    link['days'].splice(link['days'].indexOf(day), 1)
                    await fetch('/changevar', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({email: username, id: link['id'], variable: 'days', days: link['days']})
                    })
                }
                else {
                    await fetch('/delete', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({id: link['id'], email: username})
                    })
                }
                return await pause(username, user_links, sort, 46000, "load_links")
            }
            await pause(username, user_links, sort, 46000)
        }
        if (JSON.stringify(user_links) !== JSON.stringify(links)) {
            await load_links(username, sort);
        }
    }, 15000)
}


async function pause(username, links, sort, wait, action) {
    clearInterval(open)
    await sleep(wait)
    if (action === "load_links") {return load_links(username, sort)}
    start(username, links, sort)
}