const commentEditButtons = document.getElementsByClassName("btn-edit");
const commentTextArea = document.getElementById("id_body");
const commentEditForm = document.getElementById("commentForm");
const commentSubmitButton = document.getElementById("submitButton");

for (let button of commentEditButtons) {
    button.addEventListener("click", (e) => {
        let commentId = e.target.getAttribute("comment_id");
        let commentContent = document.getElementById(`comment${commentId}`).innerText;
        commentTextArea.value = commentContent;
        commentSubmitButton.innerText = "Update";
        commentEditForm.setAttribute("action", `edit_comment/${commentId}`);
    });
}