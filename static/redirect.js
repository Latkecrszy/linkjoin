function sleep(ms) {return new Promise(resolve => setTimeout(resolve, ms))}

async function NewTab(username, links) {
    try {
    while (true) {
        let date = new Date()
        let day = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[date.getDay()]
        let minute = date.getMinutes()
        if (minute.toString().length === 1) {minute = `0${minute}`}
        let time = `${date.getHours()}:${minute}`
        let start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
        let user_links = await start_json.json()
        for (let link of user_links) {
            let days = JSON.parse(link["days"].replaceAll("'", '"'))
            if (link['active'] === "false" || link['time'] !== time || !(days.includes(day))) {continue}
            if (parseInt(link['starts']) > 0) {
                await fetch(`https://linkjoin.xyz/change_var?username=${username}&id=${link['id']}&starts=${parseInt(link['starts'])-1}&var=starts`)
                await sleep(60000)
                continue
            }
            if (isNaN(link['repeat'][0])) {
                window.open(link['link'])
                if (link['repeat'] === 'never') {await fetch(`https://linkjoin.xyz/delete?id=${link['id']}`)}
                await sleep(60000)
                continue
            }
            let accept = []
            for (let x=0; x < days.length; x++) {accept.push(parseInt(link['repeat'][0])*days.length+x)}
            if (parseInt(link['occurrences']) === accept[accept.length]) {
                await fetch(`https://linkjoin.xyz/change_var?username=${username}&id=${link['id']}&occurrences=0&var=occurrences`)
                window.open(link['link'])
                await sleep(60000)
            }
            else if (accept.includes(parseInt(link['occurrences']))) {
                await fetch(`https://linkjoin.xyz/change_var?username=${username}&id=${link['id']}&occurrences=${occurrences+1}&var=occurrences`)
                window.open(link['link'])
                await sleep(60000)
            }
        }
        await sleep(15000)
        if (JSON.stringify(user_links) !== JSON.stringify(links)) {location.reload()}
    }}
    catch {location.reload()}
}

function redirect(redirect_to) {window.open("/"+redirect_to)}