
// JQUERY variable
const $body = $("body");


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


$body.on("click", "#icon", toggleLike);



/**
 * Generate a list of all cupcakes upon DOM load
 * Send a GET request via Axios
 * Iterate over the result, create a new li for each cupcake and append it to the list
 */
// async function listCupcakes() {
//     const res = await axios.get("/api/cupcakes");
//     const cupcakes = res.data.cupcakes;
//     for(const cupcake of cupcakes) {
//         $cupcakeList.append(
//             `<li class="mt-3">Cupcake number ${cupcake["id"]}
//                 <ul>
//                     <li>Flavor: ${cupcake["flavor"]}</li>
//                     <li>Size: ${cupcake["size"]}</li>
//                     <li>Rating: ${cupcake["rating"]}</li>
//                 </ul>
//                 <img src='${cupcake["image"]}' height="150" width="150">
//             </li>`
//         );
//     }
// }

// // Create a new cupcake and add to the database based on form input, without reloading the page
// $newCupcakeForm.submit(makeNewCupcake);


// /**
//  * Retrieve form data and turn it into a dictionary
//  * Include dictionary in a POST request to the cupcake API
//  * Take the JSON response, and make it into a list item, then append to the list
//  * 
//  * Note: Axios will automatically serialize the dictionary into JSON, and create header content-type of "application/json"
//  * JSON.stringify can be used to provide JSON, but the content-type must be specified
//  * source: https://masteringjs.io/tutorials/axios/post-json
//  * 
//  */
// async function makeNewCupcake(event) {
//     event.preventDefault()
//     const flavor = $("#flavor").val();
//     const size = $("#size").val()
//     const rating = $("#rating").val()
//     const image = $("#image").val()
//     const cupcake = {
//         flavor,
//         size,
//         rating,
//         image
//     }

//     const res = await axios.post("/api/cupcakes", cupcake);

//     const cupcakeData = res.data.cupcake;

//     $("#flavor").val('');
//     $("#size").val('')
//     $("#rating").val('')
//     $("#image").val('')

//     $cupcakeList.append(
//         `<li class="mt-3">Cupcake number ${cupcakeData["id"]}
//                 <ul>
//                     <li>Flavor: ${cupcakeData["flavor"]}</li>
//                     <li>Size: ${cupcakeData["size"]}</li>
//                     <li>Rating: ${cupcakeData["rating"]}</li>
//                 </ul>
//                 <img src='${cupcakeData["image"]}' height="150" width="150">
//             </li>`
//     );
// }