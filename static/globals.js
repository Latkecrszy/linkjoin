document.addEventListener("click", x => {if (x.target.matches("#hamburger") || x.target.matches("#line1")
    || x.target.matches("#line2") || x.target.matches("#line3")) {
    document.getElementById("hamburger").classList.toggle("expand")
    document.getElementById("hamburger_dropdown").classList.toggle("expand")}
})

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

window.addEventListener('beforeunload', async () => {
    if (!['login', 'signup'].includes(location.href.split('/')[location.href.split('/').length-1])) {
        await fetch('/invalidate-token', {method: 'POST', headers:  {'Content-Type': 'application/json'},
        body: JSON.stringify({'token': token})})
    }})

function disableButton(e, loader=true) {
    e.classList.add(loader ? 'disabled' : 'disabled-no-loader')
}

function enableButton(id) {
    if (document.getElementById(id)) {
        document.getElementById(id).classList.remove('disabled')
        document.getElementById(id).classList.remove('disabled-no-loader')
    }
    else {
        document.getElementsByClassName(id)[0].classList.remove('disabled')
        document.getElementsByClassName(id)[0].classList.remove('disabled-no-loader')
    }
}

// for (let document.getElementsByClassName('afterLoad').forEach(i => )