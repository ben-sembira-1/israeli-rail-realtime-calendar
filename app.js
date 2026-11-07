document.addEventListener("DOMContentLoaded", async () => {
  const originSelect = document.getElementById("origin");
  const destSelect = document.getElementById("destination");
  const resultsDiv = document.getElementById("results");
  const allUrlInput = document.getElementById("all-url");
  const firstLastUrlInput = document.getElementById("first-last-url");
  const copyBtns = document.querySelectorAll(".copy-btn");

  let routesData = null;

  // Fetch routes.json
  try {
    const response = await fetch("routes.json");
    routesData = await response.json();

    // Populate Origin Dropdown
    routesData.stations.forEach((station) => {
      const option = document.createElement("option");
      option.value = station;
      option.textContent = station;
      originSelect.appendChild(option);
    });
  } catch (e) {
    console.error("Failed to load routes.json", e);
    alert("Could not load route data. Please ensure routes.json exists.");
  }

  // Handle Origin Change
  originSelect.addEventListener("change", () => {
    const selectedOrigin = originSelect.value;

    // Clear destination dropdown
    destSelect.innerHTML =
      '<option value="" disabled selected>Select destination...</option>';
    destSelect.disabled = true;
    resultsDiv.classList.add("hidden");

    if (!selectedOrigin) return;

    // Find available destinations for this origin
    const availableDestinations = routesData.routes
      .filter((r) => r.origin === selectedOrigin)
      .map((r) => r.destination)
      .sort();

    if (availableDestinations.length > 0) {
      availableDestinations.forEach((dest) => {
        const option = document.createElement("option");
        option.value = dest;
        option.textContent = dest;
        destSelect.appendChild(option);
      });
      destSelect.disabled = false;
    }
  });

  // Handle Destination Change
  destSelect.addEventListener("change", () => {
    const origin = originSelect.value;
    const dest = destSelect.value;

    if (!origin || !dest) return;

    const route = routesData.routes.find(
      (r) => r.origin === origin && r.destination === dest,
    );

    if (route) {
      // Calculate base URL
      const baseUrl =
        window.location.href.split("index.html")[0].replace(/\/$/, "") + "/";

      const baseName = route.filename.replace(".ics", "");

      const allUrl = `${baseUrl}${baseName}.all.ics`;
      const firstLastUrl = `${baseUrl}${baseName}.first_last.ics`;

      allUrlInput.value = allUrl;
      firstLastUrlInput.value = firstLastUrl;

      // Generate webcal URL (replace http:// or https:// with webcal://)
      const webcalAllUrl = allUrl.replace(/^https?:\/\//i, "webcal://");
      const webcalFirstLastUrl = firstLastUrl.replace(
        /^https?:\/\//i,
        "webcal://",
      );

      const isAppleDevice =
        /iPad|iPhone|iPod|Mac/.test(navigator.userAgent) ||
        (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
      const googleCalAllUrl = isAppleDevice ? webcalAllUrl : allUrl;
      const googleCalFirstLastUrl = isAppleDevice
        ? webcalFirstLastUrl
        : firstLastUrl;

      // Google Calendar subscription links
      document.getElementById("all-google-btn").href =
        `https://calendar.google.com/calendar/r?cid=${encodeURIComponent(
          googleCalAllUrl,
        )}`;
      document.getElementById("first-last-google-btn").href =
        `https://calendar.google.com/calendar/r?cid=${encodeURIComponent(
          googleCalFirstLastUrl,
        )}`;

      // Default Calendar (webcal links)
      document.getElementById("all-default-btn").href = webcalAllUrl;
      document.getElementById("first-last-default-btn").href =
        webcalFirstLastUrl;

      // Handle return route
      const returnRoute = routesData.routes.find(
        (r) => r.origin === dest && r.destination === origin,
      );
      const returnSection = document.getElementById("return-section");
      if (returnRoute) {
        const returnBaseName = returnRoute.filename.replace(".ics", "");

        const returnAllUrl = `${baseUrl}${returnBaseName}.all.ics`;
        const returnFirstLastUrl = `${baseUrl}${returnBaseName}.first_last.ics`;

        document.getElementById("return-all-url").value = returnAllUrl;
        document.getElementById("return-first-last-url").value =
          returnFirstLastUrl;

        const returnWebcalAllUrl = returnAllUrl.replace(
          /^https?:\/\//i,
          "webcal://",
        );
        const returnWebcalFirstLastUrl = returnFirstLastUrl.replace(
          /^https?:\/\//i,
          "webcal://",
        );

        const returnGoogleCalAllUrl = isAppleDevice
          ? returnWebcalAllUrl
          : returnAllUrl;
        const returnGoogleCalFirstLastUrl = isAppleDevice
          ? returnWebcalFirstLastUrl
          : returnFirstLastUrl;

        document.getElementById("return-all-google-btn").href =
          `https://calendar.google.com/calendar/r?cid=${encodeURIComponent(
            returnGoogleCalAllUrl,
          )}`;
        document.getElementById("return-first-last-google-btn").href =
          `https://calendar.google.com/calendar/r?cid=${encodeURIComponent(
            returnGoogleCalFirstLastUrl,
          )}`;

        document.getElementById("return-all-default-btn").href =
          returnWebcalAllUrl;
        document.getElementById("return-first-last-default-btn").href =
          returnWebcalFirstLastUrl;

        returnSection.style.display = "block";
      } else {
        returnSection.style.display = "none";
      }

      resultsDiv.classList.remove("hidden");
    }
  });

  // Handle Copy Buttons
  copyBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      const input = document.getElementById(targetId);

      navigator.clipboard.writeText(input.value).then(() => {
        const originalText = btn.textContent;
        btn.textContent = "Copied!";
        btn.classList.add("copied");

        setTimeout(() => {
          btn.textContent = originalText;
          btn.classList.remove("copied");
        }, 2000);
      });
    });
  });
});
