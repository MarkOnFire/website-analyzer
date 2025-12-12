#Test project for test to find bad patterns and bugs across the site

## Site to investigate: 
WPR.org

## Description of bug
A failed migration script isn't bringing images into article pages properly, resulting in many article pages that have visible embed code language from a Wordpress plug-in, rather than rendering the image.

It looks like this, though the actual text might be different depending on the image: 
[[{“fid”:”1101026″,”view_mode”:”full_width”,”fields”:{“format”:”full_width”,”alignment”:””,”field_image_caption[und][0][value]”:”%3Cp%3ETom%20and%20Jerry%20milkglass%20set%20%3Cem%3E%3Ca%20href%3D%22https%3A%2F%2Fwww.flickr.com%2Fphotos%2Fjohnnyvintage%2F%22%3EJonnie%20Andersen%3C%2Fa%3E%20(CC%20BY-NC-ND%202.0)%3C%2Fem%3E%3C%2Fp%3E%0A”,”field_image_caption[und][0][format]”:”full_html”,”field_file_image_alt_text[und][0][value]”:”Tom and Jerry milkglass set”,”field_file_image_title_text[und][0][value]”:”Tom and Jerry milkglass set”},”type”:”media”,”field_deltas”:{“2”:{“format”:”full_width”,”alignment”:””,”field_image_caption[und][0][value]”:”%3Cp%3ETom%20and%20Jerry%20milkglass%20set%20%3Cem%3E%3Ca%20href%3D%22https%3A%2F%2Fwww.flickr.com%2Fphotos%2Fjohnnyvintage%2F%22%3EJonnie%20Andersen%3C%2Fa%3E%20(CC%20BY-NC-ND%202.0)%3C%2Fem%3E%3C%2Fp%3E%0A”,”field_image_caption[und][0][format]”:”full_html”,”field_file_image_alt_text[und][0][value]”:”Tom and Jerry milkglass set”,”field_file_image_title_text[und][0][value]”:”Tom and Jerry milkglass set”}},”link_text”:false,”attributes”:{“alt”:”Tom and Jerry milkglass set”,”title”:”Tom and Jerry milkglass set”,”class”:”media-element file-full-width”,”data-delta”:”2″}}]]