export default {
    init() {
        console.log("About script initialized!");
        // Example: handling a button click specific to the about page
        const alerts = document.querySelectorAll('.alert-btn');
        alerts.forEach(btn => btn.addEventListener('click', () => alert('Hello!')));
    },
    destroy() {
        console.log("Leaving About page...");
    }
};
