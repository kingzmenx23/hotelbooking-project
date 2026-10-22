    console.log("USERPAGE JS IS WORKING");


    /* =========================================================
    ANNOUNCEMENT BAR
    ========================================================= */

    const announcement = document.getElementById("announcement");
    const closeAnnouncement = document.getElementById("closeAnnouncement");

    closeAnnouncement.addEventListener("click", () => {

        announcement.style.display = "none";

        document.getElementById("navbar").style.top = "0";

    });


    /* =========================================================
    NAVBAR SCROLL EFFECT
    ========================================================= */

    // alert("JavaScript is working!");

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


    menuBtn.addEventListener("click", openMenu);

    closeMenu.addEventListener("click", closeSideMenu);

    menuOverlay.addEventListener("click", closeSideMenu);


    /* Close menu when clicking navigation links */

    document.querySelectorAll(".side-content nav a").forEach(link => {

        link.addEventListener("click", closeSideMenu);

    });


    /* =========================================================
    LOGIN MODAL
    ========================================================= */

    const loginModal = document.getElementById("loginModal");

    const loginBtn = document.getElementById("loginBtn");

    const sideLogin = document.getElementById("sideLogin");

    const closeLogin = document.getElementById("closeLogin");


    function openLogin() {

        loginModal.classList.add("active");

    }


    function closeLoginModal() {

        loginModal.classList.remove("active");

    }



    if (loginBtn) {
        loginBtn.addEventListener("click", openLogin);
    }


    sideLogin.addEventListener("click", (event) => {

        event.preventDefault();

        closeSideMenu();

        openLogin();

    });

    closeLogin.addEventListener("click", closeLoginModal);


    /* =========================================================
    REGISTER MODAL
    ========================================================= */

    const registerModal =
        document.getElementById("registerModal");

    const registerBtn =
        document.getElementById("registerBtn");

    const closeRegister =
        document.getElementById("closeRegister");

    const openRegister =
        document.getElementById("openRegister");


    function openRegisterModal() {

        loginModal.classList.remove("active");

        registerModal.classList.add("active");

    }


    function closeRegisterModal() {

        registerModal.classList.remove("active");

    }

    if (registerBtn) {
        registerBtn.addEventListener("click", openRegisterModal);
    }
    closeRegister.addEventListener("click", closeRegisterModal);

    openRegister.addEventListener("click", (event) => {

        event.preventDefault();

        openRegisterModal();

    });


    /* =========================================================
    CLOSE MODAL WHEN CLICKING OUTSIDE
    ========================================================= */

    window.addEventListener("click", (event) => {

        if (event.target === loginModal) {

            closeLoginModal();

        }

        if (event.target === registerModal) {

            closeRegisterModal();

        }

    });


    /* =========================================================
    BOOKING DATE VALIDATION
    ========================================================= */
    /* =========================================================
    BOOKING / CHECK AVAILABILITY
    ========================================================= */

    const checkIn =
        document.getElementById("checkIn");

    const checkOut =
        document.getElementById("checkOut");

    const availabilityBtn =
        document.getElementById("availabilityBtn");

    const guests =
        document.getElementById("guests");

    const loginStatus =
        document.getElementById("loginStatus");


    /* =========================================================
    LOGIN STATUS
    ========================================================= */

    const isLoggedIn =
        loginStatus &&
        loginStatus.dataset.loggedIn === "true";


    /* =========================================================
    MINIMUM DATE = TODAY
    ========================================================= */

    if (checkIn && checkOut) {

        const today =
            new Date().toISOString().split("T")[0];

        checkIn.min = today;
        checkOut.min = today;


        /* =====================================================
        CHECK-IN CHANGES
        ===================================================== */

        checkIn.addEventListener("change", () => {

            if (checkIn.value) {

                checkOut.min = checkIn.value;

                if (
                    checkOut.value &&
                    checkOut.value <= checkIn.value
                ) {

                    checkOut.value = "";

                }

            }

        });

    }


    /* =========================================================
    CHECK AVAILABILITY
    ========================================================= */

    if (availabilityBtn) {

        availabilityBtn.addEventListener("click", (event) => {

            /* -----------------------------------------
            LOGIN CHECK
            ----------------------------------------- */

            if (!isLoggedIn) {

                event.preventDefault();

                alert(
                    "Please login first to check availability."

                );

                openLogin();

                return;

            }


            /* -----------------------------------------
            GET BOOKING DATA
            ----------------------------------------- */

            const checkInValue =
                checkIn.value;

            const checkOutValue =
                checkOut.value;

            const guestsValue =
                guests.value;


            /* -----------------------------------------
            CHECK-IN
            ----------------------------------------- */

            if (!checkInValue) {

                event.preventDefault();

                alert(
                    "Please select a check-in date."
                );

                return;

            }


            /* -----------------------------------------
            CHECK-OUT
            ----------------------------------------- */

            if (!checkOutValue) {

                event.preventDefault();

                alert(
                    "Please select a check-out date."
                );

                return;

            }


            /* -----------------------------------------
            DATE VALIDATION
            ----------------------------------------- */

            const start =
                new Date(checkInValue);

            const end =
                new Date(checkOutValue);


            if (end <= start) {

                event.preventDefault();

                alert(
                    "Check-out must be after check-in."
                );

                return;

            }


            /* -----------------------------------------
            GUEST VALIDATION
            ----------------------------------------- */

            if (!guestsValue) {

                event.preventDefault();

                alert(
                    "Please select the number of guests."
                );

                return;

            }


            /* -----------------------------------------
            EVERYTHING VALID
            ----------------------------------------- */

            console.log("Booking data is valid.");

            console.log("Check-in:", checkInValue);
            console.log("Check-out:", checkOutValue);
            console.log("Guests:", guestsValue);

            /*
            DO NOT use event.preventDefault() here.

            The form will submit to Django.
            */

        });

    }
    /* =========================================================
    NEWSLETTER
    ========================================================= */

    const newsletterForm =
        document.getElementById("newsletterForm");


    newsletterForm.addEventListener("submit", (event) => {

        event.preventDefault();


        const email =
            document.getElementById("newsletterEmail").value;


        if (!email) {

            return;

        }


        alert(
            `Thank you! ${email} has been subscribed.`
        );


        newsletterForm.reset();

    });


    /* =========================================================
    HERO BUTTON
    ========================================================= */

    document.querySelector(".hero-btn")
        .addEventListener("click", () => {

            document
                .getElementById("rooms")
                .scrollIntoView({
                    behavior: "smooth"
                });

        });


    /* =========================================================
    BOOK NOW BUTTON
    ========================================================= */

    document.querySelector(".book-btn")
        .addEventListener("click", () => {

            document
                .querySelector(".booking-bar")
                .scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });

        });


    /* =========================================================
    ESC KEY
    ========================================================= */

    document.addEventListener("keydown", (event) => {

        if (event.key === "Escape") {

            closeSideMenu();

            closeLoginModal();

            closeRegisterModal();

        }

    });




