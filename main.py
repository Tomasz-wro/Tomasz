import os
import xmltodict
from functools import reduce
import operator
import argparse


# https://stackoverflow.com/a/14692747
def getFromDict(dataDict, mapList):
    return reduce(operator.getitem, mapList, dataDict)

def dict_to_file(data, output_file):

    def get_key_content(inner_data, indent=0, output_string=None):
        if output_string is None:
            output_string = ['']

        if inner_data is None:
            pass

        elif type(inner_data) == str:
            output_string[0] = output_string[0] + '\t' * indent + inner_data + '\n'

        else:
            for key in inner_data:
                output_string[0] += '\t' * indent + key + ':\n'
                get_key_content(inner_data[key], indent + 1, output_string)
    content = ['']
    get_key_content(data, 0, content)
    content = content[0]

    with open(output_file, 'w') as f:
        f.write(content)

def short_summary_to_file(data, keys):
    output_text = ''
    for key in keys:
        output_text += key[-1] + ':\t'
        output_text += '\t' + getFromDict(data, key) + '\n'
    return output_text

def open_thunderbird_email(arguments: dict):

    def get_key_and_value(key):
        if key not in arguments:
            return ''
        return '{}=\'{}\','.format(key, arguments[key])
        # return f'{key}=\'{arguments[key]}\','

    command_params = ''
    for key in ['to', 'subject', 'body', 'attachment']:
        command_params += get_key_and_value(key).replace('\t', '    ')

    command_string = 'thunderbird -compose "{}" &'.format(command_params)
    # command_string = f'thunderbird -compose "{command_params}" &'
    os.system(command_string)

def parse_xml(xml_file):
    """
    Getting data from specified xml file.
    :param xml_file: path to xml file
    :return: dict
    """
    with open(xml_file, 'r') as f:
        data = xmltodict.parse(f.read())
    return data[list(data.keys())[0]]

def get_receiver_email(nip_email_file, nip_number):
    nip_emails = {}
    with open(nip_email_file, 'r') as f:
        for line in f:
            nip, email = line.split(';')
            nip_emails[nip] = email
    if nip_number in nip_emails:
        return nip_emails[nip_number]
    return ''

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Program wczytujący pliki xml, przetwarzający do '
                    'postaci czytelnej dla człowieka i otwierający dialog '
                    'programu thunderbird z odpowiednią wiadomością email.'
    )
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')

    required.add_argument('-i', '--input', required=True,
                        type=os.path.abspath,
                        help='ścieżka do wejściowego plik xml')
    required.add_argument('-o', '--output', required=True,
                        type=os.path.abspath,
                        help='ścieżka do pliku wynikowego')

    optional.add_argument('--nip-email',
                          type=os.path.abspath,
                          help='ścieżka pliku z emailami w formacie "NUMER_NIP;EMAIL"')

    optional.add_argument('--email-subject', default='',
                          help='Temat emaila')
    optional.add_argument('--no-email', action='store_true',
                          help='nie otwieraj programu mailowego')

    return parser.parse_args()

def main():
    args = parse_arguments()

    data = parse_xml(args.input)

    dict_to_file(data, args.output)

    short_summary = short_summary_to_file(data, [
        ['ns2:ParticularRegistration', 'ns2:SingleElement', 'ns2:GoodsRecipient', 'TraderInfo', 'TraderName'],
        ['ns2:ParticularRegistration', 'ns2:SingleElement', 'ns2:GoodsRecipient', 'TraderInfo', 'TraderIdentityType'],
        ['ns2:ParticularRegistration', 'ns2:SingleElement', 'ns2:GoodsRecipient', 'TraderInfo', 'TraderIdentityNumber'],

        ['ns2:ParticularRegistration', 'ns2:SingleElement', 'ns2:SentNumber'],
        ['ns2:ParticularRegistration', 'ns2:SingleElement', 'ns2:RecipientKeyNumber']
    ])

    if args.no_email:
        return

    email = {}
    email['body'] = short_summary
    email['subject'] = args.email_subject

    if args.nip_email is not None:
        nip_number = data['ns2:ParticularRegistration']['ns2:SingleElement']['ns2:GoodsRecipient']['TraderInfo']['TraderIdentityNumber']
        email['to'] = get_receiver_email(args.nip_email, nip_number)
    open_thunderbird_email(email)

if __name__ == '__main__':
    main()
