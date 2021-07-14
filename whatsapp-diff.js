// Usage:
// 1. Create a new bookmark in your browser, and add the following code as the
// URL. (Exclude this comment)
// 2. Navigate to the first group and click the bookmark.
// 3. Navigate to the second group and click the bookmark. Open the browser
// console to see the diff output printed.

javascript: void (function() {
    var diff = function(a, b){
        console.log(`List of people in ${a.name} but not in ${b.name}`);
        var missing = [];
        a.members.map(function(name){
            if (!b.members.includes(name)){
                missing.push(name);
            }
        });
        console.log(missing.join('\n'));
    };
    var elements = document.querySelectorAll("#main span[title]"),
        group_name = elements[0].textContent,
        names = elements[1].textContent.replace(/,/g, '').split(' '),
        group = {name: group_name, members: names};

    if (! window.diffGroups) {
        window.diffGroups = [];
        window.diffGroups.push(group);
    } else {
        var group_b = window.diffGroups[0];
        window.diffGroups = undefined;
        diff(group, group_b);
        diff(group_b, group);
    }
}());
