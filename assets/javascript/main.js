document.addEventListener("DOMContentLoaded", () => {
  const workExperience = document.querySelector('.work-experience');
  const projects = document.querySelector('.projects');

  
  const handleScroll = () => {
    const windowHeight = window.innerHeight;

    
    if (workExperience.getBoundingClientRect().top < windowHeight * 0.8) {
      workExperience.style.opacity = 1;
      workExperience.style.transform = "translateY(0)";
    }

    
    if (projects.getBoundingClientRect().top < windowHeight * 0.8) {
      projects.style.opacity = 1;
      projects.style.transform = "translateY(0)";
    }
  };

  
  window.addEventListener("scroll", handleScroll);

  
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


window.addEventListener('load', function () {
  document.body.classList.add('page-loaded');
});

document.addEventListener("DOMContentLoaded", function () {
  const contactSection = document.getElementById("contact");
  contactSection.classList.add("animate__fadeInUp");
});



document.addEventListener("DOMContentLoaded", () => {
  const transitionLine = document.querySelector('.transition-line');

  const handleScroll = () => {
    const windowHeight = window.innerHeight;
    const rect = transitionLine.getBoundingClientRect();

    if (rect.top < windowHeight * 0.8 && rect.bottom > 0) {
      transitionLine.classList.add('visible'); 
    } else {
      transitionLine.classList.remove('visible'); 
    }
  };
  window.addEventListener("scroll", handleScroll);

  handleScroll();
});


