function updateTurnBar(current, max) {
  const chip = document.getElementById("turn-counter");
  if (!chip) return;
  const bar = chip.querySelector(".bar");
  const text = chip.querySelector(".txt");
  const pct = Math.min(current / max, 1) * 100;
  bar.style.width = pct + "%";
  text.textContent = `Turns: ${current}/${max}`;
}

document.addEventListener("DOMContentLoaded", () => {
  const sendSound = document.getElementById("sound-send");
  const winSound = document.getElementById("sound-win");
  const loseSound = document.getElementById("sound-lose");

  const typingIndicator = document.createElement("div");
  typingIndicator.id = "typing-indicator";
  typingIndicator.textContent = "Zaz is thinking...";
  document.querySelector("#chat")?.after(typingIndicator);

  const messages = document.querySelectorAll("#chat li");
  messages.forEach((el, i) => {
    setTimeout(() => {
      el.classList.add("chat-msg");
    }, 200 * i);
  });

  const form = document.querySelector("form");
  if (form && form.action.includes("/send")) {
    form.addEventListener("submit", () => {
      sendSound?.play();
      typingIndicator.style.display = "block";
    });

    // Simulate typing delay removal after 2.5s (when server would respond)
    setTimeout(() => {
      typingIndicator.style.display = "none";
    }, 2500);
  }

  const winText = document.querySelector(".status-win");
  const loseText = document.querySelector(".status-lose");

  if (winText) winSound?.play();
  if (loseText) loseSound?.play();
  const tc = document.getElementById("turn-counter");
  if (tc) {
    updateTurnBar(
      parseInt(tc.dataset.current, 10),
      parseInt(tc.dataset.max, 10)
    );
  }
});
