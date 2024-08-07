document.addEventListener("DOMContentLoaded", function() {
    const profileIcon = document.getElementById("profile-icon");
    const profileSidebar = document.getElementById("profile-sidebar");
    const closeProfile = document.getElementById("close-profile");

    profileIcon.addEventListener("click", function() {
        profileSidebar.style.display = "block";
    });

    closeProfile.addEventListener("click", function() {
        profileSidebar.style.display = "none";
    });
});
