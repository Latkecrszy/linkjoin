function sleep(ms) {return new Promise(resolve => setTimeout(resolve, ms))}

let restart = false
let restartBlocker = false
let open
let user_links
async function start(username, links, sort) {
    open = setInterval(async () => {
        let date = new Date()
        let day = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[date.getDay()]
        let minute = date.getMinutes()
        if (minute.toString().length === 1) {
            minute = `0${minute}`
        }
        let time = `${date.getHours()}:${minute}`
        let start_json = await fetch(`http://127.0.0.1:5002/db?username=${username}`)
        user_links = await start_json.json()
        for (let link of user_links) {
            let days = JSON.parse(link["days"].replaceAll("'", '"'))
            if (link['active'] === "false" || link['time'] !== time || !(days.includes(day))) {
                continue
            }
            if (parseInt(link['starts']) > 0) {
                await fetch(`https://linkjoin.xyz/change_var?username=${username}&id=${link['id']}&starts=${parseInt(link['starts']) - 1}&var=starts`)
                pause(username, user_links, sort)
            }
            if (isNaN(link['repeat'][0])) {
                window.open(link['link'])
                if (link['repeat'] === 'never') {
                    await fetch(`https://linkjoin.xyz/delete?id=${link['id']}`)
                    load_links(username, sort)
                }
                pause(username, user_links, sort)
            }
            let accept = []
            for (let x = 0; x < days.length; x++) {
                accept.push(parseInt(link['repeat'][0]) * days.length + x)
            }
            if (parseInt(link['occurrences']) === accept[accept.length]) {
                await fetch(`https://linkjoin.xyz/change_var?username=${username}&id=${link['id']}&occurrences=0&var=occurrences`)
                window.open(link['link'])
                pause(username, user_links, sort)
            } else if (accept.includes(parseInt(link['occurrences']))) {
                await fetch(`https://linkjoin.xyz/change_var?username=${username}&id=${link['id']}&occurrences=${occurrences + 1}&var=occurrences`)
                window.open(link['link'])
                pause(username, user_links, sort)
            }
        }
        if (JSON.stringify(user_links) !== JSON.stringify(links)) {
            console.log("refresh")
            load_links(username, sort);
        }
    }, 15000)
}


async function pause(username, links, sort) {
    clearInterval(open)
    await sleep(60000)
    start(username, links, sort)
}

function redirect(redirect_to) {window.open("/"+redirect_to)}

function terminate() {restart = true}