document.addEventListener('DOMContentLoaded', function() {
    var header = document.querySelector('.main-page-header');
    var content = document.querySelector('.content');

    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (!entry.isIntersecting) {
                header.style.display = 'none';
            } else {
                header.style.display = 'block';
            }
        });
    }, { threshold: 0 });

    observer.observe(content);
});


