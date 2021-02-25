function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  function nextDay(day) {
      days = {"1": "Mon", "2": "Tue", "3": "Wed", "4": "Thu", "5": "Fri", "6": "Sat", "7": "Sun"}
      for (const day_num in days) {
          if (days[day_num] == day) {
              if (parseInt(day_num) == 7) {
                  return "Mon"}
              else {
                  console.log(days[parseInt(day_num)+1])
                  return days[parseInt(day_num)+1]}
          }
      }
  }

  function prevDay(day) {
      days = {"1": "Mon", "2": "Tue", "3": "Wed", "4": "Thu", "5": "Fri", "6": "Sat", "7": "Sun"}
      for (const day_num in days) {
          if (days[day_num] == day) {
              if (parseInt(day_num) == 1) {
                  return "Sun"}
              else {
                  console.log(days[parseInt(day_num)-1])
                  return days[parseInt(day_num)-1]}
          }
      }
  }

async function NewTab(username) {
    while (true) {
        let date = new Date()
        console.log(date.getDay())
        let day = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}[parseInt(date.getDay())]

        let start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
        let user_links = await start_json.json()
        let link_hour;
        let link_minute;
        for (const link of user_links) {
            console.log(link)
            if (parseInt(date.getHours()) == parseInt(link["time"].split(":")[0]) && parseInt(date.getMinutes()) == parseInt(link["time"].split(":")[1])) {
                if (link['recurring'] == "true") {
                    if (link['days'].includes(day)) {
                        window.open(link["link"])
                        await sleep(60000)
                    }
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
        console.log(`day: ${day}, hour: ${parseInt(date.getHours())}, minute: ${parseInt(date.getMinutes())}`)
        await sleep(15000)
    }
}

  function redirect(redirect_to) {
      window.open("/"+redirect_to)
  }

  function timeDifference() {
      let date = new Date()
      let difference = date.getTimezoneOffset()
      console.log(difference)
      return difference-(difference*2)
  }