function showToast(message, type = "info") {
	let toastContainer = document.querySelector(".toast-container");

	// If the toast container doesn't exist, create it
	if (!toastContainer) {
		toastContainer = document.createElement("div");
		toastContainer.className = "toast-container";
		document.body.appendChild(toastContainer);
	}

	// Rest of the function remains the same
	const toastId = "toast-" + Date.now();

	const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

	toastContainer.insertAdjacentHTML("beforeend", toastHTML);

	const toastElement = document.getElementById(toastId);
	const toast = new bootstrap.Toast(toastElement, {
		animation: true,
		autohide: true,
		delay: 5000
	});

	toast.show();

	toastElement.addEventListener("hidden.bs.toast", () => {
		toastElement.remove();
	});
}