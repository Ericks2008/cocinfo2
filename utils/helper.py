def get_level_badge_class(current_level, troops_detail_item, th_level):
    if troops_detail_item and th_level in troops_detail_item:
        min_level = troops_detail_item[th_level]['min']
        max_level = troops_detail_item[th_level]['max']
        if current_level < min_level:
            return 'bg-danger'
        elif current_level == max_level:
            return 'bg-success'
        else:
            return 'bg-secondary'
    return 'bg-secondary'

