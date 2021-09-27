
// JQUERY variable for document body
const $body = $("body");


/**
 * Event handler function for message like/unlike
 * 
 * From the clicked icon:
 * Get the LI that the message belongs to - the message is contained 
 * in data-message-id
 * 
 * Then use the id in a POST request to the server add_like route
 * Lastly, toggle the icon from thumbs up to star, or vice versa
 * 
 */
async function toggleLike(evt) {

    evt.preventDefault()

    const $icon = $(evt.target);
    const $button = $($icon.closest("BUTTON"))
    const $message = $(evt.target.closest("LI"));
    const $messageId = $message.data('message-id');

    const res = await axios.post(`/users/add_like/${$messageId}`);

    console.log(res)

    //toggle icon
    if($icon.attr('class') == 'fa fa-thumbs-up') {
        $icon.attr('class', 'fa fa-star');
        $button.removeClass('btn-secondary');
        $button.addClass('btn-warning');
    } else {
        $icon.attr('class', 'fa fa-thumbs-up');
        $button.removeClass('btn-warning');
        $button.addClass('btn-secondary');
    }
}


// Click event handler
$body.on("click", "#icon", toggleLike);
