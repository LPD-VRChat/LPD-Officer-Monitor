<template>
    <div class="navbar">
        <NavbarButton name='Home' />
        <NavbarButton name='Login' />
        <NavbarButton name='Officers' />
        <NavbarButton name='Officers only' />

        <div class="dropdown">
            <button class="dropbtn">Moderation &darr;
            </button>

            <div class="dropdown-content">
                <NavbarButton name='Moderation' />
                <NavbarButton name='Leaves of Absence' />
                <NavbarButton name='VRChat Name List' />
                <NavbarButton name='Officers by Role' />
                <NavbarButton name='Inactive Officers' />
                <NavbarButton name='Patrol Time' />
                <NavbarButton name='Last Activity by Rank' />
            </div>
        </div>

        <div class="dropdown">
            <button class="dropbtn">Dispatch &darr;
            </button>

            <div class="dropdown-content">
                <NavbarButton name='Dispatch' />


            </div>
        </div>

        <a href="https://teamup.com/ksfnmscvrenv3hkk32">Event Calendar</a>


    </div>
</template>

<script>
    import NavbarButton from './NavbarButton.vue'

    export default {
        name: 'Navbar',
        props: {
            msg: String
        },
        components: {
            NavbarButton
        }
    }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
    /* Navbar container */
    .navbar {
        overflow: hidden;
        background-color: #333;
        font-family: Arial;
    }

    /* Links inside the navbar */
    .navbar a {
        float: left;
        font-size: 16px;
        color: white;
        text-align: center;
        padding: 14px 16px;
        text-decoration: none;
    }

    /* The dropdown container */
    .dropdown {
        float: left;
        overflow: hidden;
    }

    /* Dropdown button */
    .dropdown .dropbtn {
        font-size: 16px;
        border: none;
        outline: none;
        color: white;
        padding: 14px 16px;
        background-color: inherit;
        font-family: inherit;
        margin: 0;
    }

    /* Add a red background color to navbar links on hover */
    .navbar a:hover,
    .dropdown:hover .dropbtn {
        background-color: red;
    }

    /* Dropdown content (hidden by default) */
    .dropdown-content {
        display: none;
        position: absolute;
        background-color: #f9f9f9;
        min-width: 160px;
        box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.2);
        z-index: 1;
    }

    /* Links inside the dropdown */
    .dropdown-content a {
        float: none;
        color: black;
        padding: 12px 16px;
        text-decoration: none;
        display: block;
        text-align: left;
    }

    /* Add a grey background color to dropdown links on hover */
    .dropdown-content a:hover {
        background-color: #ddd;
    }

    /* Show the dropdown menu on hover */
    .dropdown:hover .dropdown-content {
        display: block;
    }
</style>