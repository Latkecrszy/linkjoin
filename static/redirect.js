let openInterval, user_links, paused

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
    if (paused) {
        return
    }
    openInterval = setInterval(async () => {
        const newDate = new Date((Date.now() + 60000*open_early))
        const day = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[newDate.getDay()]
        let minute = newDate.getMinutes()
        if (minute.toString().length === 1) {minute = `0${minute}`}
        const time = `${newDate.getHours()}:${minute}`
        for (let link of global_links['links']) {
            let days = link['days']
            if (link['active'] === "false" || link['time'] !== time || !(days.includes(day)) || (link['activated'] === 'false' &&
                new Date(link['date']).toLocaleDateString() !== new Date().toLocaleDateString())) {
                continue
            }
            window.open(link['link'])
            if (link['activated'] === 'false') {
                await fetch('/changevar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({id: link['id'], email: link['username'], variable: 'activated', activated: 'true'})
                })
            }
            if (link['repeat'] === 'never') {
                await fetch('/disable', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({id: link['id'], email: link['username']})
                })
            }
            await fetch('/analytics', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({'field': 'links_opened'})})
            await pause(username, user_links, sort, 46000)
        }
    }, 15000)
}


async function pause(username, links, sort, wait) {
    paused = true
    clearInterval(openInterval)
    await sleep(wait)
    paused = false
    start(username, links, sort)
}