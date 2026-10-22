console.log("AVAILABILITY JS IS WORKING");


/* =========================================================
   NAVBAR SCROLL EFFECT
========================================================= */

const navbar = document.getElementById("navbar");

window.addEventListener("scroll", function () {

    if (window.scrollY > 50) {

        navbar.classList.add("scrolled");

    } else {

        navbar.classList.remove("scrolled");

    }

});


/* =========================================================
   SIDE MENU
========================================================= */

const menuBtn = document.getElementById("menuBtn");
const sideMenu = document.getElementById("sideMenu");
const closeMenu = document.getElementById("closeMenu");
const menuOverlay = document.getElementById("menuOverlay");


function openMenu() {

    sideMenu.classList.add("active");
    menuOverlay.classList.add("active");

    document.body.style.overflow = "hidden";

}


function closeSideMenu() {

    sideMenu.classList.remove("active");
    menuOverlay.classList.remove("active");

    document.body.style.overflow = "";

}


if (menuBtn) {
    menuBtn.addEventListener("click", openMenu);
}

if (closeMenu) {
    closeMenu.addEventListener("click", closeSideMenu);
}

if (menuOverlay) {
    menuOverlay.addEventListener("click", closeSideMenu);
}


/* =========================================================
   CLOSE MENU WHEN CLICKING LINKS
========================================================= */

document.querySelectorAll(".side-content nav a")
    .forEach(link => {

        link.addEventListener("click", closeSideMenu);

    });


/* =========================================================
   BOOK NOW BUTTONS
========================================================= */

document.querySelectorAll(".room-book-btn")
    .forEach(button => {

        button.addEventListener("click", function () {

            console.log(
                "Selected room:",
                this.dataset.room
            );

        });

    });


/* =========================================================
   ESC KEY
========================================================= */

document.addEventListener("keydown", function (event) {

    if (event.key === "Escape") {

        closeSideMenu();

    }

});