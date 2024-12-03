document.addEventListener("DOMContentLoaded", () => {
  const workExperience = document.querySelector('.work-experience');
  const projects = document.querySelector('.projects');

  // Function to handle visibility of sections when scrolled into view
  const handleScroll = () => {
    const windowHeight = window.innerHeight;

    // Check if the work experience section is in view
    if (workExperience.getBoundingClientRect().top < windowHeight * 0.8) {
      workExperience.style.opacity = 1;
      workExperience.style.transform = "translateY(0)";
    }

    // Check if the projects section is in view
    if (projects.getBoundingClientRect().top < windowHeight * 0.8) {
      projects.style.opacity = 1;
      projects.style.transform = "translateY(0)";
    }
  };

  // Trigger on scroll
  window.addEventListener("scroll", handleScroll);

  // Initial check for elements in view when page loads
  handleScroll();
});

document.addEventListener("DOMContentLoaded", () => {
  const underlineTitle = document.querySelector(".underline-title");

  const handleScroll = () => {
    const rect = underlineTitle.getBoundingClientRect();
    const windowHeight = window.innerHeight;

    if (rect.top < windowHeight * 0.8) {
      underlineTitle.classList.add("in-view");
    } else {
      underlineTitle.classList.remove("in-view");
    }
  };

  window.addEventListener("scroll", handleScroll);
});

// Wait for the page to fully load before applying the animation
window.addEventListener('load', function () {
  document.body.classList.add('page-loaded');
});

