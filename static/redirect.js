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
    open = setInterval(async () => {
        let date = new Date()
        let day = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[date.getDay()]
        let minute = date.getMinutes()
        if (minute.toString().length === 1) {minute = `0${minute}`}
        let time = `${date.getHours()}:${minute}`
        let start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
        user_links = await start_json.json()
        for (let link of user_links) {
            let days = JSON.parse(link["days"].replaceAll("'", '"'))
            if (link['active'] === "false" || link['time'] !== time || !(days.includes(day))) {
                continue
            }
            if (parseInt(link['starts']) > 0) {
                pause(username, user_links, sort, 46000)
            }
            if (isNaN(link['repeat'][0])) {
                window.open(link['link'])
                if (link['repeat'] === 'never') {
                    await fetch(`http://127.0.0.1:5002/delete?id=${link['id']}`)
                    load_links(username, sort)
                }
                pause(username, user_links, sort, 46000)
            }
            // Work on making the linkjoin-messenger check the occurrences the way it does here
            // What this does: First, it checks if it repeats every week. No need to check for occurrences if it does.
            // Next, if it doesn't repeat every week, it checks the occurrences.
            if ('occurrences' in link) {
                let accept = []
                for (let x = 0; x < days.length; x++) {
                    accept.push(parseInt(link['repeat'][0]) * days.length + x - 1)
                }
                if (parseInt(link['occurrences']) === 0) {
                    window.open(link['link'])
                    pause(username, user_links, sort, 46000)
                } else if (accept.includes(parseInt(link['occurrences']))) {
                    window.open(link['link'])
                    pause(username, user_links, sort, 46000)
                }
            }

        }
        if (JSON.stringify(user_links) !== JSON.stringify(links)) {
            console.log("refresh")
            load_links(username, sort);
        }
    }, 15000)
}


async function pause(username, links, sort, wait) {
    clearInterval(open)
    await sleep(wait)
    start(username, links, sort)
}

function redirect(redirect_to) {window.open("/"+redirect_to)}