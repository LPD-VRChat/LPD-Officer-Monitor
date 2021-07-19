import Settings
import Keys

officers = []


def is_officer(officer_id):
    if officer_id in officers:
        return True


def create_officer(officer_id):
    officers.append(officer_id)


def remove_officer(officer_id):
    officers.remove(officer_id)


def is_any_trainer(officer_id):
    return True
