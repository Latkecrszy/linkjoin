function sleep(ms) {return new Promise(resolve => setTimeout(resolve, ms))}

let open
let user_links

function minutes(time, before){
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
    console.log("started")
    open = setInterval(async () => {
        console.log("working 1")
        let date = new Date()
        let day = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[date.getDay()]
        let minute = date.getMinutes()
        if (minute.toString().length === 1) {minute = `0${minute}`}
        let time = `${date.getHours()}:${minute}`
        console.log("working 2")
        let start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
        console.log("working 3")
        user_links = await start_json.json()
        console.log("working 4")
        for (let link of user_links) {
            let days = link['days']
            if (link['active'] === "false" || link['time'] !== time || !(days.includes(day))) {
                continue
            }
            if (parseInt(link['starts']) > 0) {
                continue
            }
            if (link['repeat'] === 'never') {
                if (link['days'].length > 1) {
                    link['days'].splice(link['days'].indexOf(day), 1)
                    console.log("working 5")
                    fetch(`/change_var?username=${username}&id=${link['id']}&var=days&days=${link['days']}`)
                    console.log("working 6")
                }
                else {
                    await window.open(link['link'])
                    fetch(`/delete?id=${link['id']}`)
                }
                console.log("did an open")
                console.log("working 7")
                return await pause(username, user_links, sort, 46000, "load_links")
            }
            console.log("working somewhere")
            window.open(link['link'])
            console.log("opened")
            console.log("working 8")
            await pause(username, user_links, sort, 46000)
        }
        if (JSON.stringify(user_links) !== JSON.stringify(links)) {
            console.log("refresh")
            await load_links(username, sort);
        }
    }, 15000)
}


async function pause(username, links, sort, wait, action) {
    clearInterval(open)
    console.log("pausing")
    await sleep(wait)
    console.log("done pausing")
    if (action === "load_links") {return load_links(username, sort)}
    start(username, links, sort)
}

function redirect(redirect_to) {window.open("/"+redirect_to)}