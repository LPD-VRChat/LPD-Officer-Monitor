<template>
    <th>{{ name }}</th>
</template>

<script>
    export default {
        name: "TableHeader",
        props: {
            name: String
        }
    }
</script>

<style>
    table.blueTable thead th {
        font-size: 15px;
        font-weight: bold;
        color: #FFFFFF;
        border-left: 2px solid #D0E4F5;
    }
</style>