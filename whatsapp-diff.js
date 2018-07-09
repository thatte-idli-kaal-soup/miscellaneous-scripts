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
