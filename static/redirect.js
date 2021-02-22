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
    let date = new Date()
    day = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}[parseInt(date.getDay())]
    hour = parseInt(date.getHours())
    minute = parseInt(date.getMinutes())
    let start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
    let user_links = await start_json.json()
    console.log(user_links)
    let link_hour;
    let link_minute;
    for (const link of user_links) {
        link_hour = parseInt(link["time"].split(":")[0])
        link_minute = parseInt(link["time"].split(":")[1])
        console.log(`days: ${link["days"]}, link_hour: ${link_hour}, link_minute: ${link_minute}`)
        if (link["days"].includes(day) && hour == link_hour && minute == link_minute-1 && link["active"] == "true") {
            window.open(link["link"])
        }
    }
    console.log(`day: ${day}, hour: ${hour}, minute: ${minute}`)
    while (true) {
        date = new Date()
        day = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}[parseInt(date.getDay())]
        hour = parseInt(date.getHours())
        minute = parseInt(date.getMinutes())
        start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
        user_links = await start_json.json()
        console.log(user_links)
        for (const link of user_links) {
            link_hour = parseInt(link["time"].split(":")[0])
            link_minute = parseInt(link["time"].split(":")[1])
            console.log(`days: ${link["days"]}, link_hour: ${link_hour}, link_minute: ${link_minute}`)
            if (link["days"].includes(day) && hour == link_hour && minute == link_minute-1 && link["active"] == "true") {
                window.open(link["link"])
                sleep(60000)
            }
        }
        console.log(`day: ${day}, hour: ${hour}, minute: ${minute}`)
        sleep(15000)
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