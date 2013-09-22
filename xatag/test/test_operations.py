import pytest
import xattr

from xatag.operations import *

NON_XATAG_TAGS = {'user.other.tag':  'something'}
XATAG_TAGS = {
    'user.org.xatag.tags': 'tag1;tag2;tag3;tag4;tag5',
    'user.org.xatag.tags.genre': 'indie;pop',
    'user.org.xatag.tags.artist': 'The XX'
    }

@pytest.fixture
def file_with_tags(tmpdir):
    f = tmpdir.join('test.txt')
    path = str(f.dirpath() + '/test.txt')
    f.open('a').close
    x = xattr.xattr(path)
    for k, v in NON_XATAG_TAGS.items():
        x[k] = v
    for k, v in XATAG_TAGS.items():
        x[k] = v
    return path

@pytest.fixture
def file_with_tags2(tmpdir):
    tags = {'user.org.xatag.tags': 'tag1;tag6',
            'user.org.xatag.tags.genre': 'good',
            'user.org.xatag.tags.other': 'yes'}

    f = tmpdir.join('test2.txt')
    path = str(f.dirpath() + '/test2.txt')
    f.open('a').close
    x = xattr.xattr(path)
    for k, v in tags.items():
        x[k] = v
    return path

def test_is_xatag_xattr_key():
    assert is_xatag_xattr_key('user.org.xatag.tags')
    assert is_xatag_xattr_key('user.org.xatag.tags.whatever')
    assert is_xatag_xattr_key('org.xatag.tags')
    assert is_xatag_xattr_key('org.xatag.tags.whatever')
    assert not is_xatag_xattr_key('anything else')

def test_xatag_to_xattr_key():
    assert xatag_to_xattr_key('') == 'user.org.xatag.tags'
    assert xatag_to_xattr_key('tags') == 'user.org.xatag.tags'
    assert xatag_to_xattr_key('other') == 'user.org.xatag.tags.other'
    tag = Tag('genre', 'classical')
    assert xatag_to_xattr_key(tag) == 'user.org.xatag.tags.genre'

# TODO
from StringIO import StringIO
def test_print_file_tags(file_with_tags):
    out = StringIO()
    print_file_tags(file_with_tags, out=out)
    output = out.getvalue().strip()
    pass

def test_read_tag_keys(file_with_tags):
    keys = read_tag_keys(file_with_tags)  
    assert sorted(keys) == sorted(['', 'genre', 'artist'])

def test_read_tags_as_dict(file_with_tags):
    tags = read_tags_as_dict(file_with_tags)  
    assert tags == {'': ['tag1','tag2','tag3','tag4','tag5'],
                    'genre': ['indie','pop'],
                    'artist': ['The XX']
                    }

def test_xattr_value_to_list():
    assert xattr_value_to_list('') == []
    assert xattr_value_to_list(' \n \t') == []
    assert xattr_value_to_list('one') == ['one']
    assert xattr_value_to_list('one tag') == ['one tag']
    assert xattr_value_to_list('one;two;three') == ['one', 'two', 'three']
    assert xattr_value_to_list('one;two words;three') == ['one', 'two words', 'three']
    assert xattr_value_to_list('one; two words   ;\nthree\t') == ['one', 'two words', 'three']

def test_list_to_xattr_value():
    assert list_to_xattr_value([]) == ''
    assert list_to_xattr_value(["one", "   two words\n"]) == 'one;two words'

def test_remove_tag_values_from_xattr_value():
    assert remove_tag_values_from_xattr_value('one', 'one') == ''
    assert remove_tag_values_from_xattr_value('one;two;three;four', ['two','four']) == 'one;three'
    assert remove_tag_values_from_xattr_value('', ['notfound']) == ''

    assert remove_tag_values_from_xattr_value('one', 'one', True) == 'one'
    assert remove_tag_values_from_xattr_value('one;two;three;four', ['two','five'], True) == 'two'
    assert remove_tag_values_from_xattr_value('one;two', [''], True) == 'one;two'
    assert remove_tag_values_from_xattr_value('', ['notfound'], True) == ''

class TestTag():
    def test___init__(self):
        t = Tag('genre', 'classical')
        assert t.key == 'genre'
        assert t.value == 'classical'
        t = Tag('', 'favorite')
        assert t.key == ''
        t = Tag('tags', 'favorite')
        assert t.key == ''

    def test_from_string(self):
        t = Tag.from_string('simple-tag')[0]
        assert t.key == ''
        assert t.value == 'simple-tag'
        t = Tag.from_string('tags:simple-tag')[0]
        assert t.key == ''
        t = Tag.from_string('genre:classical')[0]
        assert t.key == 'genre'
        assert t.value == 'classical'
        ts = Tag.from_string('genre:classical;   rock;\n bluegrass\tstuff') # Nigel Kennedy?
        assert len(ts) == 3
        assert ts[0].key == 'genre'
        assert ts[0].value == 'classical'
        assert ts[1].key == 'genre'
        assert ts[1].value == 'rock'
        assert ts[2].key == 'genre'
        assert ts[2].value == 'bluegrass stuff'
        t = Tag.from_string('multi:part:key')[0]
        assert t.key == 'multi:part'
        assert t.value == 'key'
        
    def test_to_string(self):
        t = Tag('', 'simple-tag')
        assert t.to_string() == 'simple-tag'
        t = Tag('genre', 'classical')
        assert t.to_string() == 'genre:classical'

def test_add_tags(file_with_tags):
    x = xattr.xattr(file_with_tags)
    add_tags(file_with_tags, [Tag('', 'another'), Tag('', 'zanother'), Tag('genre', 'awesome'),
                              Tag('artist', '')])
    assert x['user.org.xatag.tags'] == 'another;tag1;tag2;tag3;tag4;tag5;zanother'
    assert x['user.org.xatag.tags.artist'] == 'The XX'
    assert x['user.org.xatag.tags.genre'] == 'awesome;indie;pop'
    add_tags(file_with_tags, [Tag('unused', '')])
    assert 'user.org.xatag.tags.unused' not in x.keys()
    assert 'unused' not in read_tags_as_dict(file_with_tags)

def test_set_tags(file_with_tags):
    x = xattr.xattr(file_with_tags)
    set_tags(file_with_tags, [Tag('', 'another'), Tag('', 'zanother'), Tag('genre', 'awesome')])
    assert x['user.org.xatag.tags'] == 'another;zanother'
    assert x['user.org.xatag.tags.artist'] == 'The XX'
    assert x['user.org.xatag.tags.genre'] == 'awesome'
    set_tags(file_with_tags, [Tag('artist', '')])
    assert x['user.org.xatag.tags'] == 'another;zanother'
    assert x['user.org.xatag.tags.genre'] == 'awesome'
    assert 'user.org.xatag.tags.artist' not in x.keys()

def test_set_all_tags(file_with_tags):
    x = xattr.xattr(file_with_tags)
    set_all_tags(file_with_tags, [Tag('', 'another'), Tag('', 'zanother'), Tag('genre', 'awesome')])
    assert x['user.org.xatag.tags'] == 'another;zanother'
    assert x['user.org.xatag.tags.genre'] == 'awesome'
    assert 'user.org.xatag.tags.artist' not in x.keys()

def test_delete_these_tags(file_with_tags):
    x = xattr.xattr(file_with_tags)

    delete_tags(file_with_tags, [Tag('', 'tag4')])
    assert x['user.org.xatag.tags'] == 'tag1;tag2;tag3;tag5'
    assert x['user.org.xatag.tags.artist'] == 'The XX'
    assert x['user.org.xatag.tags.genre'] == 'indie;pop'

    delete_tags(file_with_tags, [Tag('', t) for t in ['tag2','tag4','tag5']])        
    assert x['user.org.xatag.tags'] == 'tag1;tag3'
    assert x['user.org.xatag.tags.artist'] == 'The XX'
    assert x['user.org.xatag.tags.genre'] == 'indie;pop'

    delete_tags(file_with_tags, Tag('notakey', 'tag'))

    delete_tags(file_with_tags, Tag('genre', 'pop'))
    assert x['user.org.xatag.tags.genre'] == 'indie'
    # xattr fields get deleted explicitly...
    assert 'user.org.xatag.tags.genre' in x.keys()
    delete_tags(file_with_tags, Tag('genre', ''))
    assert 'user.org.xatag.tags.genre' not in x.keys()
    # ...or by removing all of the tag values from the field
    assert 'user.org.xatag.tags.artist' in x.keys()
    assert 'user.org.xatag.tags' in x.keys()
    delete_tags(file_with_tags, [Tag('', t) for t in ['tag1','tag3']])
    delete_tags(file_with_tags, Tag('artist', 'The XX'))
    assert 'user.org.xatag.tags.artist' not in x.keys()
    assert 'user.org.xatag.tags' not in x.keys()

def test_delete_other_tags(file_with_tags):
    x = xattr.xattr(file_with_tags)

    delete_other_tags(file_with_tags, [Tag('', 'tag4'), Tag('genre', '')])
    assert 'user.org.xatag.tags.artist' not in x.keys()
    assert x['user.org.xatag.tags'] == 'tag4'
    assert x['user.org.xatag.tags.genre'] == 'indie;pop'

    delete_other_tags(file_with_tags, [Tag('', 'tag3'), Tag('genre', 'indie')])
    assert x['user.org.xatag.tags.genre'] == 'indie'
    assert 'user.org.xatag.tags' not in x.keys()

    delete_other_tags(file_with_tags, Tag('notakey', 'tag'))
    assert 'user.org.xatag.tags.genre' not in x.keys()

def test_delete_all_tags(file_with_tags):
    x = xattr.xattr(file_with_tags)
    delete_all_tags(file_with_tags)
    assert 'user.org.xatag.tags.tags' not in x.keys()
    assert 'user.org.xatag.tags.artist' not in x.keys()
    assert 'user.org.xatag.tags.genre' not in x.keys()
    assert x['user.other.tag'] == 'something'

@pytest.fixture
def tag_dict1():
    return {'': ['some', 'simple', 'tags'],
            'scope': ['home', 'work'],
            'first': ['one', 'tag'],
            'third': ['a', 'b']
            }

@pytest.fixture
def tag_dict2():
    return {'': ['some', 'other', 'tags'],
            'scope': ['hacking', 'programming'],
            'second': ['another', 'tag']
            }

@pytest.fixture
def tag_dict_with_empty_vals():
    return {'': ['some', 'simple', 'other'],
            'scope': [''],
            'second': ['another'],
            'third': ['a', 'b']
            }

def test_merge_tags(tag_dict1, tag_dict2):
    m = merge_tags(tag_dict1, tag_dict2)
    assert sorted(m['']) == sorted(['some', 'other', 'simple', 'tags'])
    assert sorted(m['scope']) == sorted(['home', 'work', 'hacking', 'programming'])
    assert sorted(m['first']) == sorted(['one', 'tag'])
    assert sorted(m['second']) == sorted(['another', 'tag'])

def test_subtract_tags(tag_dict1, tag_dict_with_empty_vals):
    s = subtract_tags(tag_dict1, tag_dict_with_empty_vals)
    assert sorted(s['']) == sorted(['tags'])
    assert 'scope' not in s.keys()
    assert s['first'] == tag_dict1['first']
    assert 'second' not in s.keys()
    assert 'third' not in s.keys()

def test_select_tags(tag_dict1, tag_dict_with_empty_vals):
    s = select_tags(tag_dict1, tag_dict_with_empty_vals)
    assert sorted(s['']) == sorted(['some', 'simple'])
    assert sorted(s['scope']) == sorted(tag_dict1['scope'])
    assert 'first' not in s.keys()
    assert 'second' not in s.keys()
    
def test_copy_tags(file_with_tags, file_with_tags2):
    d1a = read_tags_as_dict(file_with_tags)
    copy_tags(file_with_tags, file_with_tags2)
    d1b = read_tags_as_dict(file_with_tags)
    d2 = read_tags_as_dict(file_with_tags2)
    assert d1a == d1b
    assert sorted(d2['']) == sorted(['tag1', 'tag2', 'tag3', 'tag4', 'tag5', 'tag6'])
    assert sorted(d2['genre']) == sorted(['indie', 'pop', 'good'])
    assert sorted(d2['artist']) == sorted(['The XX'])
    assert sorted(d2['other']) == sorted(['yes'])

def test_copy_tags2(file_with_tags, file_with_tags2):
    tags = [Tag('', 'tag2'), Tag('genre', '')]
    d1a = read_tags_as_dict(file_with_tags)
    copy_tags(file_with_tags, file_with_tags2, tags=tags)
    d1b = read_tags_as_dict(file_with_tags)
    d2 = read_tags_as_dict(file_with_tags2)
    assert d1a == d1b
    assert sorted(d2['']) == sorted(['tag1', 'tag2', 'tag6'])
    assert sorted(d2['genre']) == sorted(['indie', 'pop', 'good'])
    assert 'artist' not in d2.keys()
    assert sorted(d2['other']) == sorted(['yes'])

def test_copy_tags3(file_with_tags, file_with_tags2):
    tags = [Tag('', 'tag2'), Tag('genre', '')]
    d1a = read_tags_as_dict(file_with_tags)
    copy_tags(file_with_tags, file_with_tags2, tags=tags, complement=True)
    d1b = read_tags_as_dict(file_with_tags)
    d2 = read_tags_as_dict(file_with_tags2)
    assert d1a == d1b
    assert sorted(d2['']) == sorted(['tag1', 'tag3', 'tag4', 'tag5', 'tag6'])
    assert sorted(d2['genre']) == sorted(['good'])
    assert sorted(d2['artist']) == sorted(['The XX'])
    assert sorted(d2['other']) == sorted(['yes'])
    
    
