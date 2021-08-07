function sleep(ms) {return new Promise(resolve => setTimeout(resolve, ms));}
document.getElementById("click_to_copy").addEventListener('click', async function copyText() {
    navigator.clipboard.writeText(document.getElementById("share_link").value).then(async () => {
        document.getElementById("click_to_copy").innerText = "Copied!"
        await sleep(2000)
        document.getElementById("click_to_copy").innerText = "Click to Copy Link"
    })
})