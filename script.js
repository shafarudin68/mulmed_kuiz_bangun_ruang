// =======================================
// TIMER QUIZ
// =======================================

const timerElement = document.getElementById("timer");

if (timerElement) {

    let time = 30;

    const form = document.querySelector("form");

    const countdown = setInterval(function () {

        time--;

        timerElement.innerHTML = time;

        if (time <= 0) {

            clearInterval(countdown);

            if (form) {

                form.submit();

            }

        }

    }, 1000);

}