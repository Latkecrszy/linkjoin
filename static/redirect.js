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

  async function NewTab(username, minute, day, hour) {
      let diff = timeDifference()
      minute = parseInt(minute)
      day = day
      hour = parseInt(hour)
      hour += Math.floor(parseInt(diff)/60)
      if (hour > 24) {
          day = nextDay(day)
          hour -= 24
      }
      else if (hour < 1) {
          day = prevDay(day)
          hour += 24
      }
      minute += parseInt(diff) % 60
      if (minute >= 60) {
          minute -= 60
          hour += 1
      }
      console.log(hour)
      console.log(minute)
      console.log(day)
      let iteration = 0
      if (minute >= 60) {
          minute -= 60
          hour += 1
          if (hour > 24) {
              day = nextDay(day)
              hour -= 24
          }
      }
      let start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
      let user_links = await start_json.json()
      console.log(user_links)
      for (const link of user_links) {
          let link_hour = parseInt(link["time"].split(":")[0])
          let link_minute = parseInt(link["time"].split(":")[1])
          console.log(`days: ${link["days"]}, link_hour: ${link_hour}, link_minute: ${link_minute}`)
          if (link["days"].includes(day) && hour == link_hour && minute == link_minute && link["active"] == "true") {
                      window.open(link["link"])
          }
      }
      console.log(`day: ${day}, hour: ${hour}, minute: ${minute}`)
      setInterval(async function() {
          iteration += 1
          minute += 1
          if (minute >= 60) {
              minute -= 60
              hour += 1
              if (hour > 24) {
                  day = nextDay(day)
                  hour -= 24
              }
          }
          let start_json = await fetch(`https://linkjoin.xyz/db?username=${username}`)
          let user_links = await start_json.json()
          console.log(user_links)
          for (const link of user_links) {
              let link_hour = parseInt(link["time"].split(":")[0])
              let link_minute = parseInt(link["time"].split(":")[1])
              console.log(`days: ${link["days"]}, link_hour: ${link_hour}, link_minute: ${link_minute}`)
              if (link["days"].includes(day) && hour == link_hour && minute == link_minute && link["active"] == "true") {
                          window.open(link["link"])
              }
          }
          console.log(`day: ${day}, hour: ${hour}, minute: ${minute}`)
          if (iteration == 1) {
            location.reload()
          }
          
      }, 60000)
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