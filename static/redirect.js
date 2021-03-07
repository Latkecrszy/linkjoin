function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
let keep_on = false
async function NewTab(username) {
    while (true) {
        let date = new Date()
        console.log(date.getDay())
        let day = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"}[parseInt(date.getDay())]
        let start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
        let user_links = await start_json.json()
        let link_hour;
        let link_minute;
        let days;
        for (const link of user_links) {
            console.log(link)
            days = JSON.parse(link["days"].replaceAll("'", '"'))
            if (parseInt(date.getHours()) == parseInt(link["time"].split(":")[0]) && parseInt(date.getMinutes()) == parseInt(link["time"].split(":")[1]) && link['active'] == "true") {
                if (days.includes(day)) {
                    if (parseInt(['starts']) >= 0) {

                    }
                    if (link['repeat'] == "week") {
                        window.open(link["link"])
                        await sleep(60000)
                    }
                    else if (link['repeat'] == "2 weeks") {
                        if (link['occurrences'] == 1*days.length) {
                            window.open(link["link"])
                            location.href = `/change_var?username=${username}&id=${link['id']}&var=occurrences&occurrences=0`
                        }
                        else {
                            location.href = `/change_var?username=${username}&id=${link['id']}&occurrences=1&var=occurrences`
                        }
                        await sleep(60000)
                    }
                    else if (link['repeat'] == "3 weeks") {
                        if (link['occurrences'] == 2*days.length) {
                            window.open(link["link"])
                            location.href = `/change_var?username=${username}&id=${link['id']}&occurrences=0&var=occurrences`
                        }
                        else {
                            location.href = `/change_var?username=${username}&id=${link['id']}&occurrences=${link['occurrences']+1}&var=occurrences`
                        }
                        await sleep(60000)
                    }
                    else if (link['repeat'] == "4 weeks") {
                        if (link['occurrences'] == 3*days.length) {
                            window.open(link["link"])
                            location.href = `/change_var?username=${username}&id=${link['id']}&occurrences=0&var=occurrences`
                        }
                        else {
                            location.href = `/change_var?username=${username}&id=${link['id']}&occurrences=${link['occurrences']+1}&var=occurrences`
                        }
                        await sleep(60000)
                    }
                    else if (link['repeat'] == "month") {
                        prevMonth = date.getMonth()-1
                        if (parseInt(link['occurrences']) == date.getMonth() && parseInt(link['occurrences'])-1 == prevMonth) {
                            window.open(link["link"])
                            newMonth = parseInt(link['occurrences'])+1
                            if (newMonth > 11) {
                                newMonth = 0
                            }
                            location.href = `/change_var?username=${username}&id=${link['id']}&occurrences=${newMonth}&var=occurrences`
                        }
                        await sleep(60000)
                    }
                    else {
                        for (let date_info of JSON.parse(link['dates'].replaceAll("'", '"'))) {
                            console.log(date.getMonth())
                            console.log(date.getFullYear())
                            console.log(date.getDate())
                            console.log(date_info.month)
                            console.log(date_info.year)
                            console.log(date_info.day)
                            if (parseInt(date_info.month)-1 == parseInt(date.getMonth()) && parseInt(date_info.year) == parseInt(date.getFullYear()) && parseInt(date_info.day) == parseInt(date.getDate())) {
                                window.open(link["link"])
                                await sleep(60000)
                            }
                        }
                    }
                }
            }
        }
        console.log(date.getDay())
        console.log(`day: ${day}, hour: ${parseInt(date.getHours())}, minute: ${parseInt(date.getMinutes())}`)
        await sleep(15000)
        if (keep_on == true) {
            location.reload()
        }
    }
}

function redirect(redirect_to) {
    window.open("/"+redirect_to)
}

function change_keep_on() {
    if (keep_on == false) {
        keep_on = true
    }
    else {
        keep_on = false
    }
    console.log(keep_on)
}