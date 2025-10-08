// Set the date/time of last win
const lastWin = new Date('2011-01-16T00:00:00'); // adjust time if you want

function updateTimer() {
  const now = new Date();
  let diffMs = now - lastWin; // milliseconds

  // calculate units
  const seconds = Math.floor(diffMs / 1000 % 60);
  const minutes = Math.floor(diffMs / (1000 * 60) % 60);
  const hours = Math.floor(diffMs / (1000 * 60 * 60) % 24);
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24) % 365);
  const years = Math.floor(diffMs / (1000 * 60 * 60 * 24 * 365));

  // format
  const formatted = `${years} yrs, ${days} days, ${hours}h ${minutes}m ${seconds}s`;
  document.getElementById('timer').textContent = formatted;
}

// Initial update
updateTimer();
// Then update every second if you want the seconds ticking
setInterval(updateTimer, 1000);