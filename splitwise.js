// Browser snippet to create a new Splitwise group

// 1. Go to the edit page of a group
// 2. Run this javascript in the console

var names = [
    // ['Name', 'Email'],
];

names.map(function([name, email]){
    document.querySelector('.add_nested_fields').click();
});

names.map(function([name, email], i){
    console.log(i, name, email);
    document.querySelectorAll('.name')[i].value = name;
    document.querySelectorAll('.email')[i].value = email;
});
