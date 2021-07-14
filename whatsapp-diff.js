// Usage:
// 1. Create a new bookmark in your browser, and add the following code as the
// URL. (Exclude this comment)
// 2. Navigate to the first group and click the bookmark.
// 3. Navigate to the second group and click the bookmark. Open the browser
// console to see the diff output printed.

javascript: void (function () {
    var diff = function (a, b) {
        const msg = `List of people in ${a.name} but not in ${b.name}`;
        var missing = [];
        a.members.map(function (name) {
            if (!b.members.includes(name)) {
                missing.push(name);
            }
        });
        const names = missing.join('\n');
        const count = `${missing.length} people`;
        console.log(`${msg}\n${names}\n${count}`);
    };
    var elements = document.querySelectorAll('#main span[title]'),
        group_name = elements[0].textContent,
        names = elements[1].textContent.replace(/ /g, '').split(','),
        group = { name: group_name, members: names };

    if (!window.diffGroups) {
        window.diffGroups = [];
        window.diffGroups.push(group);
        console.log('Captured info for first group');
    } else {
        var group_b = window.diffGroups[0];
        window.diffGroups = undefined;
        diff(group, group_b);
        diff(group_b, group);
    }
})();
