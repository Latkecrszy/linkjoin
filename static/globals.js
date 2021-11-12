document.addEventListener("click", x => {if (x.target.matches("#hamburger") || x.target.matches("#line1") || x.target.matches("#line2") || x.target.matches("#line3")) {document.getElementById("hamburger").classList.toggle("expand"); document.getElementById("hamburger_dropdown").classList.toggle("expand")}})

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
}

window.addEventListener('unload', async () => {console.log('unloading'); await fetch('/invalidate-token', {
    method: 'POST',
    headers:  {'Content-Type': 'application/json'},
    body: JSON.stringify({'token': token})
    }
)})

// for (let document.getElementsByClassName('afterLoad').forEach(i => )