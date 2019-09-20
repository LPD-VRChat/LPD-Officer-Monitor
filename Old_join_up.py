    if message.channel.name == "join-up":
        LPD_role = await getRoleByName(settings["main_role"], message.guild)
        Mod_role = await getRoleByName(settings["mod_role"], message.guild)

        # If the message is from a moderator, ignore the message
        if Mod_role in message.author.roles or message.author.id in settings["Other_admins"] or message.author.bot is True:
            return
        
        # Check if this message is from an LPD member, if so, remove it
        if LPD_role in message.author.roles:

            if not message.author.dm_channel:
                await message.author.create_dm()
            await message.author.dm_channel.send(settings["main_role"]+" members cannot send to the "+message.channel.mention+" channel")
            
            await message.delete()
            return
        
        # This is a join up application

        # Make sure the message is the right length
        lines = message.content.count('\n') + 1
        if lines != settings["num_of_application_lines"]:
            await removeJoinUpApplication(message, "please check the line spacing.")
            return

        # Make sure the person applying has not sent an application already
        all_applications = 0
        async for old_message in message.channel.history(limit=None):
            if old_message.author == message.author and old_message.id != message.id:
                await removeJoinUpApplication(message, "You have already applied in "+message.channel.mention+", you cannot apply again until your application has been reviewed but you can edit your current application", False)
                return

            # This counts the nuber of applications
            if Mod_role not in old_message.author.roles and old_message.author.id not in settings["Other_admins"] and message.author.bot is not True:
                all_applications += 1
                
        print("Number of applications:",all_applications)
        
        # This closes the applications after a set amount of applications
        if all_applications >= settings["max_applications"]:
            await message.channel.send("We are not accepting more applications until the current applications have been reviewed")
            
            # Lock the channel for the @everyone role
            everyone_role = await getRoleByName("@everyone", message.guild)
            overwrites = message.channel.overwrites
            
            if everyone_role in overwrites: overwrite = overwrites[everyone_role]
            else: overwrite = discord.PermissionOverwrite()

            overwrite.update(send_messages = False)

            await message.channel.set_permissions(everyone_role, overwrite=overwrite)
